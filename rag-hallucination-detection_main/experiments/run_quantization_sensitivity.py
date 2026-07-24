"""
experiments/run_quantization_sensitivity.py — Phase 5 #6
========================================================

Does the refinement paradox survive aggressive quantization?

Practitioners deploy quantized models (Q4_0, Q5_K_M, Q8_0) for cost.
If Q4 hides the paradox, that's a finding. If Q4 *amplifies* it, that's
a bigger finding (cheaper models = more vulnerable).

We hold retrieval fixed (MiniLM + HCPC stack at top_k=3) and sweep the
generator's quantization level via Ollama's tag system:

    mistral:7b-instruct-q4_0      ~4.4 GB  (current default)
    mistral:7b-instruct-q5_K_M    ~5.2 GB
    mistral:7b-instruct-q8_0      ~7.7 GB
    mistral:7b-instruct-fp16      ~14 GB   (only on machines with the RAM)

Outputs:
    results/quantization_sensitivity/per_query.csv
    results/quantization_sensitivity/summary.csv
    results/quantization_sensitivity/paradox_by_quant.csv
    results/quantization_sensitivity/summary.md
    results/quantization_sensitivity/completed_tuples.json   (resume)

Run (default: Q4 vs Q5 vs Q8 only — skips fp16 for memory):
    ollama serve &
    ollama pull mistral:7b-instruct-q4_0
    ollama pull mistral:7b-instruct-q5_K_M
    ollama pull mistral:7b-instruct-q8_0
    python3 experiments/run_quantization_sensitivity.py \\
        --quants q4_0 q5_K_M q8_0 \\
        --datasets squad pubmedqa \\
        --n_questions 30

Estimated wall clock: 3 quants × 3 conds × 2 datasets × 30 q × ~3 s/call
= ~1.4 hr on M4. Q8 is slower than Q4 by ~2× so total may reach 2 hr.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

from src.dataset_loaders        import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline           import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever         import HCPCRetriever
from src.hcpc_v2_retriever      import HCPCv2Retriever
from src.retrieval_metrics      import compute_retrieval_quality

OUT_DIR    = "results/quantization_sensitivity"
CHECKPOINT = os.path.join(OUT_DIR, "completed_tuples.json")
CHUNK_SIZE = 1024
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

V1_SIM, V1_CE = 0.50,  0.00
V2_SIM, V2_CE = 0.45, -0.20

# Map a short alias the user types to the actual Ollama tag.
QUANT_TAGS = {
    # NOTE: Ollama's `mistral:latest` IS the q4_0 build; the explicit
    # `mistral:7b-instruct-q4_0` tag isn't published on Ollama Hub
    # (only q5_K_M, q8_0, fp16 are). Map q4_0 to mistral:latest.
    "q4_0":   "mistral:latest",
    "q5_K_M": "mistral:7b-instruct-q5_K_M",
    "q8_0":   "mistral:7b-instruct-q8_0",
    "fp16":   "mistral:7b-instruct-fp16",
}


def _load_checkpoint() -> Dict[str, bool]:
    if os.path.exists(CHECKPOINT):
        return json.load(open(CHECKPOINT))
    return {}


def _save_checkpoint(s):
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(s, open(CHECKPOINT, "w"), indent=2)


def _eval(pipeline, qa, retriever, label, detector):
    if retriever is None:
        docs, _ = pipeline.retrieve_with_scores(qa["question"])
        hlog = {}
    else:
        out = retriever.retrieve(qa["question"])
        docs, hlog = out if isinstance(out, tuple) else (out, {})
    gen = pipeline.generate(qa["question"], docs)
    nli = detector.detect(gen["answer"], gen["context"])
    rm = compute_retrieval_quality(qa["question"], docs, pipeline.embeddings)
    return {
        "question":            qa["question"],
        "ground_truth":        qa.get("ground_truth", ""),
        "answer":              gen["answer"],
        "condition":           label,
        "faithfulness_score":  nli["faithfulness_score"],
        "is_hallucination":    nli["is_hallucination"],
        "mean_retrieval_similarity": rm.get("mean_similarity", 0.0),
        "refined":             bool(hlog.get("refined", False))
                                if isinstance(hlog, dict) else False,
        "ccs":                 hlog.get("context_coherence", -1.0)
                                if isinstance(hlog, dict) else -1.0,
        "latency_s":           gen["latency_s"],
    }


def run_tuple(dataset, quant_alias, n_q, detector):
    tag = QUANT_TAGS.get(quant_alias, quant_alias)
    print(f"\n{'='*72}\n[Quant] {dataset.upper()} × {tag}\n{'='*72}")
    docs, qa = load_dataset_by_name(dataset, max_papers=30)
    if not docs or not qa:
        return []

    coll = f"quant_{dataset}_{quant_alias}"
    pipe = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=3,
        model_name=tag,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_quant/{coll}",
    )
    pipe.index_documents(docs, collection_name=coll)
    v1 = HCPCRetriever(pipeline=pipe, sim_threshold=V1_SIM,
                        ce_threshold=V1_CE, top_k=3)
    v2 = HCPCv2Retriever(pipeline=pipe, sim_threshold=V2_SIM,
                          ce_threshold=V2_CE, top_k_protected=2,
                          max_refine=2)

    rows = []
    for qa_pair in qa[:n_q]:
        for label, retr in [("baseline", None), ("hcpc_v1", v1), ("hcpc_v2", v2)]:
            try:
                r = _eval(pipe, qa_pair, retr, label, detector)
                r["dataset"] = dataset
                r["quant"]   = quant_alias
                r["model_tag"] = tag
                rows.append(r)
            except Exception as exc:
                print(f"[Quant] err {dataset}/{quant_alias}/{label}: {exc}")
    return rows


def aggregate(rows):
    df = pd.DataFrame(rows)
    if df.empty: return df
    g = df.groupby(["dataset", "quant", "condition"])
    s = g.agg(
        n_queries=("question", "count"),
        faith=("faithfulness_score", "mean"),
        halluc=("is_hallucination", "mean"),
        sim=("mean_retrieval_similarity", "mean"),
        refine_rate=("refined", "mean"),
        ccs=("ccs", lambda x: float(x[x>=0].mean()) if (x>=0).any() else float("nan")),
        latency=("latency_s", "mean"),
    ).reset_index()
    for c in ("faith","halluc","sim","refine_rate","ccs","latency"):
        s[c] = s[c].round(4)
    return s


def paradox_by_quant(summary):
    rows = []
    for (ds, q), sub in summary.groupby(["dataset", "quant"]):
        try:
            base = sub[sub["condition"] == "baseline"].iloc[0]
            v1   = sub[sub["condition"] == "hcpc_v1"].iloc[0]
            v2   = sub[sub["condition"] == "hcpc_v2"].iloc[0]
        except IndexError:
            continue
        rows.append({
            "dataset":     ds,
            "quant":       q,
            "faith_base":  base["faith"],
            "faith_v1":    v1["faith"],
            "faith_v2":    v2["faith"],
            "paradox":     round(base["faith"] - v1["faith"], 4),
            "v2_recovery": round(v2["faith"] - v1["faith"], 4),
            "latency_base": base["latency"],
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quants",   nargs="+", default=["q4_0", "q5_K_M", "q8_0"])
    ap.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa"])
    ap.add_argument("--n_questions", type=int, default=30)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    state = _load_checkpoint()
    detector = HallucinationDetector()

    all_rows = []
    prior = os.path.join(OUT_DIR, "per_query.csv")
    if os.path.exists(prior):
        try: all_rows.extend(pd.read_csv(prior).to_dict("records"))
        except Exception: pass

    for ds in args.datasets:
        if ds not in DATASET_REGISTRY:
            print(f"[Quant] unknown dataset {ds}, skipping"); continue
        for q in args.quants:
            key = f"{ds}__{q}"
            if state.get(key) and not args.force:
                print(f"[Quant] checkpoint hit {key}"); continue
            rows = run_tuple(ds, q, args.n_questions, detector)
            all_rows.extend(rows)
            pd.DataFrame(rows).to_csv(
                os.path.join(OUT_DIR, f"{key}_per_query.csv"), index=False)
            state[key] = True
            _save_checkpoint(state)

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUT_DIR, "per_query.csv"), index=False)
    s = aggregate(all_rows)
    s.to_csv(os.path.join(OUT_DIR, "summary.csv"), index=False)
    p = paradox_by_quant(s)
    p.to_csv(os.path.join(OUT_DIR, "paradox_by_quant.csv"), index=False)

    md = ["# Quantization sensitivity ablation (Phase 5 #6)", "",
          "## Aggregated metrics", "", s.to_markdown(index=False) if not s.empty else "(no data)",
          "", "## Paradox by quantization", "",
          p.to_markdown(index=False) if not p.empty else "(no data)"]
    open(os.path.join(OUT_DIR, "summary.md"), "w").write("\n".join(md))
    print(f"\n[Quant] outputs -> {OUT_DIR}/")


if __name__ == "__main__":
    main()
