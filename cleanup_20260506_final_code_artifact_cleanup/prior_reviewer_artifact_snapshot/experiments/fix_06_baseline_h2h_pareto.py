"""
Fix 6: proper baseline head-to-head.

Runs HCPC-v2 vs Self-RAG vs CRAG vs RAPTOR-2L on SQuAD and HotpotQA with
matched generator where applicable, plus latency and indexing-cost logging.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiments.revision_utils import ensure_dirs, make_llm, write_markdown_table
from src.crag_retriever import CRAGRetriever
from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.hallucination_detector import HallucinationDetector
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.rag_pipeline import RAGPipeline
from src.raptor_retriever import RAPTORRetriever


OUT_DATA = Path("data/revision/fix_06")
OUT_RESULTS = Path("results/revision/fix_06")


def eval_retriever(pipe: RAGPipeline, detector: HallucinationDetector, qa: dict,
                   name: str, retriever: Any) -> Dict[str, Any]:
    t0 = time.time()
    docs, log = retriever.retrieve(qa["question"])
    retrieval_latency = time.time() - t0
    t1 = time.time()
    gen = pipe.generate(qa["question"], docs)
    generation_latency = time.time() - t1
    nli = detector.detect(gen["answer"], gen["context"])
    return {
        "condition": name,
        "question": qa["question"],
        "ground_truth": qa.get("ground_truth", ""),
        "answer": gen["answer"],
        "faithfulness_score": float(nli["faithfulness_score"]),
        "is_hallucination": bool(nli["is_hallucination"]),
        "retrieval_latency_ms": round(retrieval_latency * 1000, 3),
        "generation_latency_ms": round(generation_latency * 1000, 3),
        "total_latency_ms": round((retrieval_latency + generation_latency) * 1000, 3),
        "indexing_cost_note": log.get("indexing_cost_note", "") if isinstance(log, dict) else "",
    }


def eval_selfrag(pipe: RAGPipeline, detector: HallucinationDetector, qa: dict,
                 selfrag: Any) -> Dict[str, Any]:
    docs, _ = pipe.retrieve_with_scores(qa["question"])
    t0 = time.time()
    gen = selfrag.generate(qa["question"], docs)
    generation_latency = time.time() - t0
    nli = detector.detect(gen["answer"], gen["context"])
    return {
        "condition": "selfrag",
        "question": qa["question"],
        "ground_truth": qa.get("ground_truth", ""),
        "answer": gen["answer"],
        "faithfulness_score": float(nli["faithfulness_score"]),
        "is_hallucination": bool(nli["is_hallucination"]),
        "retrieval_latency_ms": 0.0,
        "generation_latency_ms": round(generation_latency * 1000, 3),
        "total_latency_ms": round(generation_latency * 1000, 3),
        "indexing_cost_note": "Self-RAG fine-tuned checkpoint; no extra corpus index beyond dense retrieval.",
    }


def run_dataset(args: argparse.Namespace, dataset: str, detector: HallucinationDetector) -> List[Dict[str, Any]]:
    docs, qa_pairs = load_dataset_by_name(dataset, max_papers=args.max_contexts)
    qa_use = qa_pairs[: min(args.n, len(qa_pairs))]
    partial_path = OUT_DATA / f"per_query_{dataset}_partial.csv"
    pipe = RAGPipeline(
        chunk_size=1024,
        chunk_overlap=100,
        top_k=3,
        model_name=args.model,
        persist_dir=f"./chroma_db_fix06/{dataset}",
    )
    t_index0 = time.time()
    pipe.index_documents(docs, collection_name=f"fix06_{dataset}")
    base_index_s = time.time() - t_index0
    pipe.llm = make_llm(args.backend, args.model, temperature=0.0)

    t_rap0 = time.time()
    raptor = RAPTORRetriever(pipe, docs=docs, n_clusters=args.raptor_clusters, top_k=3)
    # Force tree build before latency measurement.
    raptor._ensure_tree()
    raptor_index_s = time.time() - t_rap0
    h2h = {
        "hcpc_v2": HCPCv2Retriever(pipe, sim_threshold=0.45, ce_threshold=-0.20,
                                   top_k_protected=2, max_refine=2),
        "crag": CRAGRetriever(pipe),
        "raptor_2l": raptor,
    }
    selfrag = None
    if args.include_selfrag:
        from src.selfrag_wrapper import SelfRAGGenerator

        selfrag = SelfRAGGenerator(
            model_name=args.selfrag_model,
            load_in_8bit=args.selfrag_8bit,
            load_in_4bit=args.selfrag_4bit,
        )

    rows: List[Dict[str, Any]] = []
    for q_idx, qa in enumerate(qa_use, start=1):
        for name, retr in h2h.items():
            try:
                row = eval_retriever(pipe, detector, qa, name, retr)
                row.update({
                    "dataset": dataset,
                    "model": args.model,
                    "base_index_s": round(base_index_s, 3),
                    "raptor_index_s": round(raptor_index_s, 3),
                })
                rows.append(row)
            except Exception as exc:
                rows.append({"dataset": dataset, "condition": name, "question": qa.get("question", ""), "error": str(exc)})
        if selfrag is not None:
            try:
                row = eval_selfrag(pipe, detector, qa, selfrag)
                row.update({
                    "dataset": dataset,
                    "model": args.selfrag_model,
                    "base_index_s": round(base_index_s, 3),
                    "raptor_index_s": round(raptor_index_s, 3),
                })
                rows.append(row)
            except Exception as exc:
                rows.append({"dataset": dataset, "condition": "selfrag", "question": qa.get("question", ""), "error": str(exc)})
        if q_idx == 1 or q_idx % args.save_every == 0 or q_idx == len(qa_use):
            pd.DataFrame(rows).to_csv(partial_path, index=False)
            print(f"[Fix06] {dataset}: {q_idx}/{len(qa_use)} queries rows={len(rows)}")
    return rows


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    ok = df[df["error"].fillna("").eq("")].copy() if "error" in df.columns else df.copy()
    out = ok.groupby(["dataset", "condition"]).agg(
        n=("question", "count"),
        faithfulness=("faithfulness_score", "mean"),
        hallucination_rate=("is_hallucination", "mean"),
        p99_latency_ms=("total_latency_ms", lambda x: float(np.quantile(x, 0.99))),
        mean_latency_ms=("total_latency_ms", "mean"),
        base_index_s=("base_index_s", "max"),
        raptor_index_s=("raptor_index_s", "max"),
    ).reset_index()
    for col in ["faithfulness", "hallucination_rate", "p99_latency_ms", "mean_latency_ms", "base_index_s", "raptor_index_s"]:
        out[col] = out[col].round(6)
    out["wall_clock_cost_per_1k_queries_s"] = (out["mean_latency_ms"] / 1000 * 1000).round(3)
    return out


def plot_pareto(summary: pd.DataFrame) -> None:
    if summary.empty:
        return
    fig, ax = plt.subplots(figsize=(5.5, 4.0))
    for _, row in summary.iterrows():
        ax.scatter(row["p99_latency_ms"], row["faithfulness"], s=45)
        ax.text(row["p99_latency_ms"], row["faithfulness"], f" {row['dataset']}:{row['condition']}", fontsize=7)
    ax.set_xlabel("p99 latency (ms)")
    ax.set_ylabel("faithfulness")
    ax.set_title("Faithfulness vs latency")
    fig.tight_layout()
    fig.savefig(OUT_RESULTS / "pareto_faithfulness_latency.pdf")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["squad", "hotpotqa"])
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--max_contexts", type=int, default=250)
    parser.add_argument("--backend", choices=["ollama", "together", "groq"], default="ollama")
    parser.add_argument("--model", default="mistral")
    parser.add_argument("--raptor_clusters", type=int, default=6)
    parser.add_argument("--include_selfrag", action="store_true")
    parser.add_argument("--selfrag_model", default="selfrag/selfrag_llama2_7b")
    parser.add_argument("--selfrag_8bit", action="store_true")
    parser.add_argument("--selfrag_4bit", action="store_true")
    parser.add_argument("--save_every", type=int, default=10)
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS)
    detector = HallucinationDetector()
    rows: List[Dict[str, Any]] = []
    for dataset in args.datasets:
        if dataset in DATASET_REGISTRY:
            rows.extend(run_dataset(args, dataset, detector))
            pd.DataFrame(rows).to_csv(OUT_DATA / "per_query.csv", index=False)
    df = pd.DataFrame(rows)
    summary = summarize(df)
    df.to_csv(OUT_DATA / "per_query.csv", index=False)
    summary.to_csv(OUT_RESULTS / "h2h_summary.csv", index=False)
    plot_pareto(summary)
    write_markdown_table(OUT_RESULTS / "summary.md", "Fix 6 - baseline head-to-head", {"Summary": summary})


if __name__ == "__main__":
    main()
