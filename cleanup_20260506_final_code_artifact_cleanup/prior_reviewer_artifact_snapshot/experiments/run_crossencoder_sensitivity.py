"""
experiments/run_crossencoder_sensitivity.py — Phase 5 #8
========================================================

Does HCPC-v2's recovery depend on the specific cross-encoder reranker?

We swap the reranker (held fixed at MiniLM-L-6-v2 elsewhere in the
paper) through a panel and re-measure paradox + recovery. Robustness
check: if the recovery story holds across rerankers, the result
generalises beyond our specific choice.

Cross-encoders tested:
    cross-encoder/ms-marco-MiniLM-L-6-v2     (default, ~80 MB)
    cross-encoder/ms-marco-MiniLM-L-12-v2    (larger, ~133 MB)
    BAAI/bge-reranker-base                    (different family, ~278 MB)

Output:
    results/crossencoder_sensitivity/{per_query,summary,paradox_by_ce}.csv
    results/crossencoder_sensitivity/summary.md

Run:
    python3 experiments/run_crossencoder_sensitivity.py \\
        --rerankers cross-encoder/ms-marco-MiniLM-L-6-v2 \\
                    cross-encoder/ms-marco-MiniLM-L-12-v2 \\
                    BAAI/bge-reranker-base \\
        --datasets squad pubmedqa --n_questions 30

Estimated wall clock: 3 rerankers × 3 conds × 2 datasets × 30 q × ~3 s
= ~1.4 hr on M4. First run downloads each model (~500 MB total).
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

OUT_DIR    = "results/crossencoder_sensitivity"
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
    }


def run_tuple(ds, ce, n_q, det):
    print(f"\n{'='*72}\n[CE] {ds.upper()} × {ce}\n{'='*72}")
    docs, qa = load_dataset_by_name(ds, max_papers=30)
    if not docs or not qa: return []

    coll = f"ce_{ds}_{ce.replace('/', '_').replace('-', '_')}"
    pipe = RAGPipeline(
        chunk_size=1024, chunk_overlap=100, top_k=3,
        model_name="mistral", embed_model=EMBED,
        persist_dir=f"./chroma_db_ce/{coll}",
    )
    pipe.index_documents(docs, collection_name=coll)
    # Override the CE in both retrievers
    v1 = HCPCRetriever(pipeline=pipe, sim_threshold=V1_SIM, ce_threshold=V1_CE,
                        top_k=3, ce_model_name=ce)
    v2 = HCPCv2Retriever(pipeline=pipe, sim_threshold=V2_SIM, ce_threshold=V2_CE,
                          top_k_protected=2, max_refine=2, ce_model_name=ce)

    rows = []
    for qa_pair in qa[:n_q]:
        for label, retr in [("baseline", None), ("hcpc_v1", v1), ("hcpc_v2", v2)]:
            try:
                r = _eval(pipe, qa_pair, retr, label, det)
                r["dataset"], r["reranker"] = ds, ce
                rows.append(r)
            except Exception as e:
                print(f"[CE] err {ds}/{ce}/{label}: {e}")
    return rows


def aggregate(rows):
    df = pd.DataFrame(rows)
    if df.empty: return df
    g = df.groupby(["dataset", "reranker", "condition"])
    s = g.agg(
        n_queries=("question", "count"),
        faith=("faithfulness_score", "mean"),
        halluc=("is_hallucination", "mean"),
        sim=("mean_retrieval_similarity", "mean"),
        refine_rate=("refined", "mean"),
        ccs=("ccs", lambda x: float(x[x>=0].mean()) if (x>=0).any() else float("nan")),
    ).reset_index()
    for c in ("faith","halluc","sim","refine_rate","ccs"):
        s[c] = s[c].round(4)
    return s


def paradox_by_ce(s):
    rows = []
    for (ds, ce), sub in s.groupby(["dataset", "reranker"]):
        try:
            b = sub[sub["condition"]=="baseline"].iloc[0]
            v1 = sub[sub["condition"]=="hcpc_v1"].iloc[0]
            v2 = sub[sub["condition"]=="hcpc_v2"].iloc[0]
        except IndexError: continue
        rows.append({
            "dataset": ds, "reranker": ce,
            "faith_base": b["faith"], "faith_v1": v1["faith"], "faith_v2": v2["faith"],
            "paradox": round(b["faith"] - v1["faith"], 4),
            "v2_recovery": round(v2["faith"] - v1["faith"], 4),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rerankers", nargs="+", default=[
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "cross-encoder/ms-marco-MiniLM-L-12-v2",
        "BAAI/bge-reranker-base",
    ])
    ap.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa"])
    ap.add_argument("--n_questions", type=int, default=30)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

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
            print(f"[CE] unknown {ds}"); continue
        for ce in args.rerankers:
            key = f"{ds}__{ce.replace('/', '_')}"
            if state.get(key) and not args.force:
                print(f"[CE] checkpoint hit {key}"); continue
            rows = run_tuple(ds, ce, args.n_questions, det)
            all_rows.extend(rows)
            pd.DataFrame(rows).to_csv(
                os.path.join(OUT_DIR, f"{key.replace('-', '_')}_per_query.csv"),
                index=False)
            state[key] = True
            json.dump(state, open(CHECKPOINT, "w"), indent=2)

    df = pd.DataFrame(all_rows); df.to_csv(os.path.join(OUT_DIR, "per_query.csv"), index=False)
    s = aggregate(all_rows); s.to_csv(os.path.join(OUT_DIR, "summary.csv"), index=False)
    p = paradox_by_ce(s); p.to_csv(os.path.join(OUT_DIR, "paradox_by_ce.csv"), index=False)
    md = ["# Cross-encoder sensitivity (Phase 5 #8)", "",
          "## Paradox by reranker", "",
          p.to_markdown(index=False) if not p.empty else "(no data)"]
    open(os.path.join(OUT_DIR, "summary.md"), "w").write("\n".join(md))
    print(f"\n[CE] outputs -> {OUT_DIR}/")


if __name__ == "__main__":
    main()
