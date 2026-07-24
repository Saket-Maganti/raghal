"""
experiments/run_temperature_sensitivity.py — Phase 5 #7
========================================================

Does sampling temperature interact with the coherence paradox?

We test paradox = faith(baseline) − faith(HCPC-v1) at T ∈ {0.0, 0.3, 0.7, 1.0}.

Hypothesis (coherence theory): higher T pushes the generator toward its
parametric prior (more sampling diversity), which could either:
  - amplify the paradox (T high + fragmented context = more invention), or
  - mask it (T high adds noise that drowns out the coherence signal)

Either way, deployers run T > 0 in production and we tested T = 0.1
elsewhere. This experiment closes the gap.

Backends:
    --backend ollama  (default; uses local Mistral via OllamaLLM)
    --backend groq    (uses Groq free-tier API; ~10× faster, ideal for Kaggle)

Outputs:
    results/temperature_sensitivity/per_query.csv
    results/temperature_sensitivity/summary.csv
    results/temperature_sensitivity/paradox_by_temp.csv
    results/temperature_sensitivity/summary.md

Run (local Ollama):
    ollama serve &
    python3 experiments/run_temperature_sensitivity.py \\
        --temps 0.0 0.3 0.7 1.0 --datasets squad pubmedqa --n_questions 30
    # Estimated: 4 temps × 3 conds × 2 datasets × 30 q × 3 s = ~1.8 hr

Run (Groq, free, ~10× faster):
    export GROQ_API_KEY=...
    python3 experiments/run_temperature_sensitivity.py \\
        --backend groq --model llama-3.3-70b \\
        --temps 0.0 0.3 0.7 1.0 --datasets squad pubmedqa --n_questions 30
    # Estimated: ~12 min total
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

OUT_DIR    = "results/temperature_sensitivity"
CHECKPOINT = os.path.join(OUT_DIR, "completed_tuples.json")
EMBED      = "sentence-transformers/all-MiniLM-L6-v2"
V1_SIM, V1_CE = 0.50, 0.00
V2_SIM, V2_CE = 0.45, -0.20


def _eval(pipe, qa, retr, label, det):
    if retr is None:
        docs, _ = pipe.retrieve_with_scores(qa["question"]); hlog = {}
    else:
        out = retr.retrieve(qa["question"])
        docs, hlog = out if isinstance(out, tuple) else (out, {})
    g = pipe.generate(qa["question"], docs)
    n = det.detect(g["answer"], g["context"])
    rm = compute_retrieval_quality(qa["question"], docs, pipe.embeddings)
    return {
        "question": qa["question"],
        "ground_truth": qa.get("ground_truth", ""),
        "answer": g["answer"],
        "condition": label,
        "faithfulness_score": n["faithfulness_score"],
        "is_hallucination": n["is_hallucination"],
        "mean_retrieval_similarity": rm.get("mean_similarity", 0.0),
        "refined": bool(hlog.get("refined", False)) if isinstance(hlog, dict) else False,
        "ccs": hlog.get("context_coherence", -1.0) if isinstance(hlog, dict) else -1.0,
        "latency_s": g["latency_s"],
    }


def _make_llm(backend, model, temperature):
    if backend == "groq":
        from src.groq_llm import GroqLLM
        return GroqLLM(model=model, temperature=temperature)
    # Default: Ollama via langchain-ollama (already in pipeline)
    return None  # signal: pipeline.llm gets reset via temperature override below


def run_tuple(ds, temp, backend, model, n_q, det):
    print(f"\n{'='*72}\n[Temp] {ds.upper()} × T={temp} × {backend}/{model}\n{'='*72}")
    docs, qa = load_dataset_by_name(ds, max_papers=30)
    if not docs or not qa: return []

    coll = f"temp_{ds}_T{temp}_{model.replace('-', '_').replace('.', '_')}"
    pipe = RAGPipeline(
        chunk_size=1024, chunk_overlap=100, top_k=3,
        model_name=model, embed_model=EMBED,
        persist_dir=f"./chroma_db_temp/{coll}",
    )
    pipe.index_documents(docs, collection_name=coll)

    if backend == "groq":
        from src.groq_llm import GroqLLM
        pipe.llm = GroqLLM(model=model, temperature=temp)
    else:
        # Ollama path: rebuild pipe.llm with the new temperature
        from langchain_ollama import OllamaLLM
        pipe.llm = OllamaLLM(model=model, temperature=temp)

    v1 = HCPCRetriever(pipeline=pipe, sim_threshold=V1_SIM, ce_threshold=V1_CE, top_k=3)
    v2 = HCPCv2Retriever(pipeline=pipe, sim_threshold=V2_SIM, ce_threshold=V2_CE,
                          top_k_protected=2, max_refine=2)

    rows = []
    for qa_pair in qa[:n_q]:
        for label, retr in [("baseline", None), ("hcpc_v1", v1), ("hcpc_v2", v2)]:
            try:
                r = _eval(pipe, qa_pair, retr, label, det)
                r["dataset"], r["temperature"], r["backend"], r["model"] = ds, temp, backend, model
                rows.append(r)
            except Exception as e:
                print(f"[Temp] err {ds}/T{temp}/{label}: {e}")
    return rows


def aggregate(rows):
    df = pd.DataFrame(rows)
    if df.empty: return df
    g = df.groupby(["dataset", "temperature", "condition"])
    s = g.agg(
        n_queries=("question", "count"),
        faith=("faithfulness_score", "mean"),
        halluc=("is_hallucination", "mean"),
        ccs=("ccs", lambda x: float(x[x>=0].mean()) if (x>=0).any() else float("nan")),
        latency=("latency_s", "mean"),
    ).reset_index()
    for c in ("faith","halluc","ccs","latency"):
        s[c] = s[c].round(4)
    return s


def paradox_by_temp(s):
    rows = []
    for (ds, T), sub in s.groupby(["dataset", "temperature"]):
        try:
            b = sub[sub["condition"]=="baseline"].iloc[0]
            v1 = sub[sub["condition"]=="hcpc_v1"].iloc[0]
            v2 = sub[sub["condition"]=="hcpc_v2"].iloc[0]
        except IndexError: continue
        rows.append({
            "dataset": ds, "temperature": T,
            "faith_base": b["faith"], "faith_v1": v1["faith"], "faith_v2": v2["faith"],
            "paradox": round(b["faith"] - v1["faith"], 4),
            "v2_recovery": round(v2["faith"] - v1["faith"], 4),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--temps", nargs="+", type=float, default=[0.0, 0.3, 0.7, 1.0])
    ap.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa"])
    ap.add_argument("--backend", choices=["ollama", "groq"], default="ollama")
    ap.add_argument("--model", default=None,
                    help="model name; defaults to 'mistral' for ollama, "
                         "'llama-3.3-70b' for groq")
    ap.add_argument("--n_questions", type=int, default=30)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.model is None:
        args.model = "mistral" if args.backend == "ollama" else "llama-3.3-70b"

    os.makedirs(OUT_DIR, exist_ok=True)
    state = json.load(open(CHECKPOINT)) if os.path.exists(CHECKPOINT) else {}
    det = HallucinationDetector()

    all_rows = []
    prior = os.path.join(OUT_DIR, "per_query.csv")
    if os.path.exists(prior):
        try: all_rows.extend(pd.read_csv(prior).to_dict("records"))
        except Exception: pass

    for ds in args.datasets:
        if ds not in DATASET_REGISTRY:
            print(f"[Temp] unknown {ds}"); continue
        for T in args.temps:
            key = f"{ds}__T{T}__{args.backend}__{args.model}"
            if state.get(key) and not args.force:
                print(f"[Temp] checkpoint hit {key}"); continue
            rows = run_tuple(ds, T, args.backend, args.model, args.n_questions, det)
            all_rows.extend(rows)
            pd.DataFrame(rows).to_csv(
                os.path.join(OUT_DIR, f"{key.replace('.','_')}_per_query.csv"),
                index=False)
            state[key] = True
            json.dump(state, open(CHECKPOINT, "w"), indent=2)

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUT_DIR, "per_query.csv"), index=False)
    s = aggregate(all_rows); s.to_csv(os.path.join(OUT_DIR, "summary.csv"), index=False)
    p = paradox_by_temp(s); p.to_csv(os.path.join(OUT_DIR, "paradox_by_temp.csv"), index=False)
    md = ["# Temperature sensitivity (Phase 5 #7)", "",
          f"Backend: {args.backend}, Model: {args.model}", "",
          "## Paradox by temperature", "",
          p.to_markdown(index=False) if not p.empty else "(no data)"]
    open(os.path.join(OUT_DIR, "summary.md"), "w").write("\n".join(md))
    print(f"\n[Temp] outputs -> {OUT_DIR}/")


if __name__ == "__main__":
    main()
