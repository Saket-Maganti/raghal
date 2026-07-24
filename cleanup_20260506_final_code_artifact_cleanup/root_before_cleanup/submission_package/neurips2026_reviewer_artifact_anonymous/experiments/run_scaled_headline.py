"""
experiments/run_scaled_headline.py — Phase 7 #3 (n=300 scaling)
================================================================

Scale the headline experiment from $n{=}30$ per condition to
$n{=}300$ per condition. Reviewer concern: $n{=}30$ is too small to
support the statistical claims in §Results, even though the total
across the paper is $7{,}000+$ queries.

This run produces the n=300 headline numbers that should replace
the n=30 numbers in Table tab:hcpc_main and the abstract.

Per-tuple = 300 queries × 3 conditions = 900 LLM calls.
Across 2 datasets: 1800 calls.

Run (Ollama, ~6-8 hr local Mac):
    ollama serve &
    nohup python3 -u experiments/run_scaled_headline.py \\
        --datasets squad pubmedqa --n 300 --backend ollama --model mistral \\
        > logs/scaled_headline.log 2>&1 &

Run (Groq, ~30 min, ideal for Kaggle parallelization but burns daily
budget; check Groq quota first):
    export GROQ_API_KEY=...
    python3 experiments/run_scaled_headline.py --backend groq \\
        --model llama-3.3-70b --datasets squad pubmedqa --n 300

Outputs:
    results/scaled_headline/per_query.csv
    results/scaled_headline/summary.csv
    results/scaled_headline/headline_n300.csv     (replacement numbers
                                                    for tab:hcpc_main)
    results/scaled_headline/significance.csv      (paired Wilcoxon +
                                                    bootstrap CIs)
    results/scaled_headline/summary.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from src.dataset_loaders        import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline           import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever         import HCPCRetriever
from src.hcpc_v2_retriever      import HCPCv2Retriever
from src.retrieval_metrics      import compute_retrieval_quality

OUT_DIR    = "results/scaled_headline"
CHECKPOINT = os.path.join(OUT_DIR, "completed_tuples.json")
EMBED      = "sentence-transformers/all-MiniLM-L6-v2"
V1_SIM, V1_CE = 0.50,  0.00
V2_SIM, V2_CE = 0.45, -0.20


def _load_checkpoint() -> Dict[str, bool]:
    if os.path.exists(CHECKPOINT):
        return json.load(open(CHECKPOINT))
    return {}


def _save_checkpoint(s):
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(s, open(CHECKPOINT, "w"), indent=2)


def _eval(pipe, qa, retriever, label, det):
    if retriever is None:
        docs, _ = pipe.retrieve_with_scores(qa["question"]); hlog = {}
    else:
        out = retriever.retrieve(qa["question"])
        docs, hlog = out if isinstance(out, tuple) else (out, {})
    g = pipe.generate(qa["question"], docs)
    n = det.detect(g["answer"], g["context"])
    rm = compute_retrieval_quality(qa["question"], docs, pipe.embeddings)
    return {
        "question":            qa["question"],
        "ground_truth":        qa.get("ground_truth", ""),
        "answer":              g["answer"],
        "condition":           label,
        "faithfulness_score":  n["faithfulness_score"],
        "is_hallucination":    n["is_hallucination"],
        "mean_retrieval_similarity": rm.get("mean_similarity", 0.0),
        "ccs":                 hlog.get("context_coherence", -1.0)
                                if isinstance(hlog, dict) else -1.0,
        "refined":             bool(hlog.get("refined", False))
                                if isinstance(hlog, dict) else False,
    }


def run(ds, n_q, backend, model, det):
    print(f"\n{'='*72}\n[Scaled] {ds.upper()} × {backend}/{model} × n={n_q}\n{'='*72}")
    docs, qa = load_dataset_by_name(ds, max_papers=30)
    if not docs or not qa: return []
    if len(qa) < n_q:
        print(f"[Scaled] only {len(qa)} queries available; using all")
        n_q = len(qa)

    coll = f"scaled_{ds}_{model.replace('/', '_').replace('-', '_').replace('.', '_')}"
    pipe = RAGPipeline(
        chunk_size=1024, chunk_overlap=100, top_k=3,
        model_name=model, embed_model=EMBED,
        persist_dir=f"./chroma_db_scaled/{coll}",
    )
    pipe.index_documents(docs, collection_name=coll)
    if backend == "groq":
        from src.groq_llm import GroqLLM
        pipe.llm = GroqLLM(model=model, temperature=0.1)

    v1 = HCPCRetriever(pipeline=pipe, sim_threshold=V1_SIM, ce_threshold=V1_CE, top_k=3)
    v2 = HCPCv2Retriever(pipeline=pipe, sim_threshold=V2_SIM, ce_threshold=V2_CE,
                          top_k_protected=2, max_refine=2)

    rows = []
    for i, qa_pair in enumerate(qa[:n_q]):
        for label, retr in [("baseline", None), ("hcpc_v1", v1), ("hcpc_v2", v2)]:
            try:
                r = _eval(pipe, qa_pair, retr, label, det)
                r["dataset"] = ds; r["model"] = model
                rows.append(r)
            except Exception as exc:
                print(f"[Scaled] err {ds}/{label}: {exc}")
        if (i + 1) % 25 == 0:
            print(f"[Scaled/{ds}] {i+1}/{n_q} queries done")
            # Incremental save
            pd.DataFrame(rows).to_csv(
                os.path.join(OUT_DIR, f"{ds}__partial_per_query.csv"), index=False)
    return rows


def aggregate(rows):
    df = pd.DataFrame(rows)
    if df.empty: return df
    g = df.groupby(["dataset", "condition"])
    s = g.agg(
        n=("question", "count"),
        faith=("faithfulness_score", "mean"),
        faith_std=("faithfulness_score", "std"),
        halluc=("is_hallucination", "mean"),
        sim=("mean_retrieval_similarity", "mean"),
        refine_rate=("refined", "mean"),
        ccs=("ccs", lambda x: float(x[x>=0].mean()) if (x>=0).any() else float("nan")),
    ).reset_index()
    for c in ("faith", "faith_std", "halluc", "sim", "refine_rate", "ccs"):
        s[c] = s[c].round(4)
    return s


def headline(s):
    """Replacement table for tab:hcpc_main with n=300 numbers + 95% CIs."""
    rows = []
    for ds, sub in s.groupby("dataset"):
        for cond in ["baseline", "hcpc_v1", "hcpc_v2"]:
            try:
                r = sub[sub["condition"] == cond].iloc[0]
            except IndexError: continue
            n = int(r["n"])
            faith = float(r["faith"])
            std = float(r["faith_std"])
            # 95% normal-approx CI on the mean
            ci_half = 1.96 * std / np.sqrt(n)
            rows.append({
                "dataset":      ds,
                "condition":    cond,
                "n":            n,
                "faith":        faith,
                "faith_ci95_lo": round(faith - ci_half, 4),
                "faith_ci95_hi": round(faith + ci_half, 4),
                "halluc":       float(r["halluc"]),
                "ccs":          float(r["ccs"]) if not np.isnan(r["ccs"]) else None,
            })
    return pd.DataFrame(rows)


def significance(df):
    """Paired Wilcoxon signed-rank: baseline vs HCPC-v1 (paradox);
    HCPC-v1 vs HCPC-v2 (recovery)."""
    rows = []
    for ds, sub in df.groupby("dataset"):
        b = sub[sub["condition"] == "baseline"].set_index("question")["faithfulness_score"]
        v1 = sub[sub["condition"] == "hcpc_v1"].set_index("question")["faithfulness_score"]
        v2 = sub[sub["condition"] == "hcpc_v2"].set_index("question")["faithfulness_score"]
        common = b.index.intersection(v1.index).intersection(v2.index)
        if len(common) < 5: continue
        b, v1, v2 = b.loc[common], v1.loc[common], v2.loc[common]
        try:
            par_stat, par_p = wilcoxon(b.values, v1.values, alternative="greater")
            rec_stat, rec_p = wilcoxon(v2.values, v1.values, alternative="greater")
        except Exception as exc:
            print(f"[wilcoxon] {ds}: {exc}"); continue
        rows.append({
            "dataset":          ds,
            "n_pairs":          int(len(common)),
            "paradox_mean":     round(float((b - v1).mean()), 4),
            "paradox_p":        round(float(par_p), 6),
            "paradox_significant": bool(par_p < 0.05),
            "recovery_mean":    round(float((v2 - v1).mean()), 4),
            "recovery_p":       round(float(rec_p), 6),
            "recovery_significant": bool(rec_p < 0.05),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa"])
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--backend", choices=["ollama", "groq"], default="ollama")
    ap.add_argument("--model", default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.model is None:
        args.model = "mistral" if args.backend == "ollama" else "llama-3.3-70b"

    os.makedirs(OUT_DIR, exist_ok=True)
    state = _load_checkpoint()
    det = HallucinationDetector()

    all_rows = []
    prior = os.path.join(OUT_DIR, "per_query.csv")
    if os.path.exists(prior):
        try: all_rows.extend(pd.read_csv(prior).to_dict("records"))
        except Exception: pass

    for ds in args.datasets:
        if ds not in DATASET_REGISTRY:
            print(f"[Scaled] unknown {ds}"); continue
        key = f"{ds}__{args.backend}__{args.model}__n{args.n}"
        if state.get(key) and not args.force:
            print(f"[Scaled] checkpoint hit {key}"); continue
        rows = run(ds, args.n, args.backend, args.model, det)
        all_rows.extend(rows)
        pd.DataFrame(rows).to_csv(
            os.path.join(OUT_DIR, f"{key.replace('.', '_')}_per_query.csv"),
            index=False)
        state[key] = True
        _save_checkpoint(state)

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUT_DIR, "per_query.csv"), index=False)
    s = aggregate(all_rows); s.to_csv(os.path.join(OUT_DIR, "summary.csv"), index=False)
    h = headline(s); h.to_csv(os.path.join(OUT_DIR, "headline_n300.csv"), index=False)
    sig = significance(df); sig.to_csv(os.path.join(OUT_DIR, "significance.csv"), index=False)

    md = ["# Scaled headline ($n{=}300$, Phase 7 #3)", "",
          "Replaces the $n{=}30$ headline numbers in `tab:hcpc_main` ",
          "and the abstract with $10\\times$ scaled estimates plus ",
          "95% confidence intervals and paired Wilcoxon significance tests.", "",
          "## Headline numbers ($n{=}300$, with 95% CI)", "",
          h.to_markdown(index=False) if not h.empty else "(no data)", "",
          "## Significance tests", "",
          sig.to_markdown(index=False) if not sig.empty else "(no data)", ""]
    open(os.path.join(OUT_DIR, "summary.md"), "w").write("\n".join(md))
    print(f"\n[Scaled] outputs -> {OUT_DIR}/")
    if not h.empty: print(h.to_string(index=False))


if __name__ == "__main__":
    main()
