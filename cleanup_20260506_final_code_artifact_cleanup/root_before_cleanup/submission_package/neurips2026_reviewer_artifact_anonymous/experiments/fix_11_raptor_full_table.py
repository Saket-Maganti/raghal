"""
Fix 11: RAPTOR full table.

Builds a per-dataset RAPTOR table with faithfulness, hallucination, indexing
cost, index size, and query latency.  This is the P2 polish version of the
RAPTOR comparison.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd

from experiments.revision_utils import ensure_dirs, make_llm, write_markdown_table
from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.hallucination_detector import HallucinationDetector
from src.rag_pipeline import RAGPipeline
from src.raptor_retriever import RAPTORRetriever


OUT_DATA = Path("data/revision/fix_11")
OUT_RESULTS = Path("results/revision/fix_11")


def dir_size_mb(path: str | Path) -> float:
    total = 0
    path = Path(path)
    if not path.exists():
        return 0.0
    for root, _dirs, files in os.walk(path):
        for file in files:
            total += (Path(root) / file).stat().st_size
    return total / (1024 * 1024)


def run_dataset(args: argparse.Namespace, dataset: str, detector: HallucinationDetector) -> tuple[list[dict], dict]:
    print(
        f"[Fix11] starting dataset={dataset} n={args.n} "
        f"max_contexts={args.max_contexts} backend={args.backend} model={args.model}",
        flush=True,
    )
    docs, qa_pairs = load_dataset_by_name(dataset, max_papers=args.max_contexts)
    persist = Path(f"./chroma_db_fix11/{dataset}")
    pipe = RAGPipeline(
        chunk_size=1024,
        chunk_overlap=100,
        top_k=3,
        model_name=args.model,
        persist_dir=str(persist),
    )
    t0 = time.time()
    pipe.index_documents(docs, collection_name=f"fix11_{dataset}")
    dense_index_s = time.time() - t0
    pipe.llm = make_llm(args.backend, args.model, temperature=0.0)
    raptor = RAPTORRetriever(pipe, docs=docs, n_clusters=args.raptor_clusters, top_k=3)
    t1 = time.time()
    raptor._ensure_tree()
    raptor_index_s = time.time() - t1

    rows: List[Dict[str, Any]] = []
    qa_use = qa_pairs[: min(args.n, len(qa_pairs))]
    for idx, qa in enumerate(qa_use, start=1):
        if idx == 1 or idx % max(1, args.save_every) == 0:
            print(f"[Fix11] {dataset} query {idx}/{len(qa_use)} rows={len(rows)}", flush=True)
        q0 = time.time()
        retrieved, log = raptor.retrieve(qa["question"])
        ret_ms = (time.time() - q0) * 1000
        g0 = time.time()
        gen = pipe.generate(qa["question"], retrieved)
        gen_ms = (time.time() - g0) * 1000
        nli = detector.detect(gen["answer"], gen["context"])
        rows.append({
            "dataset": dataset,
            "query_index": idx - 1,
            "question": qa["question"],
            "ground_truth": qa.get("ground_truth", ""),
            "faithfulness_score": float(nli["faithfulness_score"]),
            "is_hallucination": bool(nli["is_hallucination"]),
            "retrieval_latency_ms": round(ret_ms, 3),
            "generation_latency_ms": round(gen_ms, 3),
            "total_latency_ms": round(ret_ms + gen_ms, 3),
            "n_leaves_returned": log.get("n_leaves_returned", np.nan) if isinstance(log, dict) else np.nan,
            "n_summaries_returned": log.get("n_summaries_returned", np.nan) if isinstance(log, dict) else np.nan,
        })
        if idx % max(1, args.save_every) == 0:
            pd.DataFrame(rows).to_csv(OUT_DATA / f"per_query_{dataset}_partial.csv", index=False)
            print(f"[Fix11] saved partial dataset={dataset} rows={len(rows)}", flush=True)
    meta = {
        "dataset": dataset,
        "dense_index_s": round(dense_index_s, 3),
        "raptor_index_s": round(raptor_index_s, 3),
        "index_size_mb": round(dir_size_mb(persist), 3),
        "raptor_clusters": args.raptor_clusters,
    }
    return rows, meta


def summarize(rows: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    agg = rows.groupby("dataset").agg(
        n=("question", "count"),
        faithfulness=("faithfulness_score", "mean"),
        hallucination_rate=("is_hallucination", "mean"),
        p50_latency_ms=("total_latency_ms", "median"),
        p99_latency_ms=("total_latency_ms", lambda x: float(np.quantile(x, 0.99))),
    ).reset_index()
    out = agg.merge(meta, on="dataset", how="left")
    for col in out.columns:
        if col != "dataset":
            out[col] = pd.to_numeric(out[col], errors="ignore")
    return out.round(6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa", "hotpotqa"])
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--max_contexts", type=int, default=150)
    parser.add_argument("--backend", choices=["ollama", "together", "groq"], default="ollama")
    parser.add_argument("--model", default="mistral")
    parser.add_argument("--raptor_clusters", type=int, default=6)
    parser.add_argument("--save_every", type=int, default=10)
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS)
    detector = HallucinationDetector()
    all_rows: List[Dict[str, Any]] = []
    metas: List[Dict[str, Any]] = []
    for dataset in args.datasets:
        if dataset not in DATASET_REGISTRY:
            continue
        rows, meta = run_dataset(args, dataset, detector)
        all_rows.extend(rows)
        metas.append(meta)
        pd.DataFrame(all_rows).to_csv(OUT_DATA / "per_query.csv", index=False)
    df = pd.DataFrame(all_rows)
    meta_df = pd.DataFrame(metas)
    table = summarize(df, meta_df)
    df.to_csv(OUT_DATA / "per_query.csv", index=False)
    meta_df.to_csv(OUT_RESULTS / "raptor_indexing_costs.csv", index=False)
    table.to_csv(OUT_RESULTS / "raptor_full_table.csv", index=False)
    write_markdown_table(OUT_RESULTS / "summary.md", "Fix 11 - RAPTOR full table", {"RAPTOR Full Table": table})


if __name__ == "__main__":
    main()
