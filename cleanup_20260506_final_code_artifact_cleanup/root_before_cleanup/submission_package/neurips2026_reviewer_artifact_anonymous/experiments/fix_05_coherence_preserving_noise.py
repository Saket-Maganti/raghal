"""
Fix 5: coherence-preserving noise slope response.

Compares three perturbations on SQuAD:
    1. random off-topic noise;
    2. same-topic, answer-absent noise from the query's top-20 pool;
    3. HCPC-v1 refinement.

The aim is to test whether the paradox is distinct from generic retrieval
quality degradation.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from langchain_core.documents import Document

from experiments.revision_utils import ensure_dirs, make_llm, write_markdown_table
from src.dataset_loaders import load_dataset_by_name
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.rag_pipeline import RAGPipeline
from src.retrieval_metrics import compute_retrieval_quality


OUT_DATA = Path("data/revision/fix_05")
OUT_RESULTS = Path("results/revision/fix_05")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def answer_absent(doc: Document, answer: str) -> bool:
    ans = (answer or "").strip().lower()
    if not ans:
        return True
    return ans not in doc.page_content.lower()


def random_pool(source_docs: list[Document], base_docs: list[Document], rng: random.Random) -> list[Document]:
    base_ids = {d.metadata.get("paper_id", "") for d in base_docs}
    pool = [d for d in source_docs if d.metadata.get("paper_id", "") not in base_ids]
    rng.shuffle(pool)
    return pool


def eval_docs(pipe: RAGPipeline, detector: HallucinationDetector, qa: dict,
              docs: list[Document], condition: str, extra: dict[str, Any]) -> Dict[str, Any]:
    gen = pipe.generate(qa["question"], docs)
    nli = detector.detect(gen["answer"], gen["context"])
    rm = compute_retrieval_quality(qa["question"], docs, pipe.embeddings)
    return {
        "condition": condition,
        "question": qa["question"],
        "ground_truth": qa.get("ground_truth", ""),
        "answer": gen["answer"],
        "context": gen["context"],
        "faithfulness_score": float(nli["faithfulness_score"]),
        "is_hallucination": bool(nli["is_hallucination"]),
        "mean_retrieval_similarity": float(rm.get("mean_similarity", 0.0)),
        **extra,
    }


def run(args: argparse.Namespace) -> pd.DataFrame:
    print(
        f"[Fix05] starting n={args.n} seed={args.seed} "
        f"max_contexts={args.max_contexts} backend={args.backend} model={args.model}",
        flush=True,
    )
    docs, qa_pairs = load_dataset_by_name("squad", max_papers=args.max_contexts)
    rng = random.Random(args.seed)
    qa_use = list(qa_pairs)
    rng.shuffle(qa_use)
    qa_use = qa_use[: min(args.n, len(qa_use))]
    pipe = RAGPipeline(
        chunk_size=1024,
        chunk_overlap=100,
        top_k=3,
        model_name=args.model,
        embed_model=EMBED_MODEL,
        persist_dir="./chroma_db_fix05/squad",
    )
    pipe.index_documents(docs, collection_name="fix05_squad")
    pipe.llm = make_llm(args.backend, args.model, temperature=0.0)
    detector = HallucinationDetector()
    v1 = HCPCRetriever(pipeline=pipe, sim_threshold=0.50, ce_threshold=0.00, top_k=3)
    rows: List[Dict[str, Any]] = []

    for i, qa in enumerate(qa_use, start=1):
        if i == 1 or i % max(1, args.save_every) == 0:
            print(f"[Fix05] query {i}/{len(qa_use)} rows={len(rows)}", flush=True)
        base_docs, _ = pipe.retrieve_with_scores(qa["question"])
        top20_old = pipe.top_k
        pipe.top_k = 20
        top20, _ = pipe.retrieve_with_scores(qa["question"])
        pipe.top_k = top20_old

        same_topic = [
            d for d in top20
            if d.page_content not in {b.page_content for b in base_docs}
            and answer_absent(d, qa.get("ground_truth", ""))
        ]
        rand_pool = random_pool(docs, base_docs, rng)

        for n_noise in args.n_noise:
            # Keep first k-n original docs, replace tail with noise.
            k = len(base_docs)
            nrep = min(n_noise, k)
            random_docs = list(base_docs[: k - nrep]) + rand_pool[:nrep]
            coherent_docs = list(base_docs[: k - nrep]) + same_topic[:nrep]
            if len(random_docs) == k:
                rows.append(eval_docs(pipe, detector, qa, random_docs, "random_noise", {
                    "n_noise": nrep,
                    "noise_rate": nrep / k,
                }))
            if len(coherent_docs) == k:
                rows.append(eval_docs(pipe, detector, qa, coherent_docs, "coherent_uninformative_noise", {
                    "n_noise": nrep,
                    "noise_rate": nrep / k,
                }))
        rows.append(eval_docs(pipe, detector, qa, base_docs, "baseline", {"n_noise": 0, "noise_rate": 0.0}))
        try:
            v1_docs, vlog = v1.retrieve(qa["question"])
            rows.append(eval_docs(pipe, detector, qa, v1_docs, "hcpc_v1_refinement", {
                "n_noise": np.nan,
                "noise_rate": np.nan,
                "refined": bool(vlog.get("refined", True)) if isinstance(vlog, dict) else True,
            }))
        except Exception as exc:
            rows.append({"condition": "hcpc_v1_refinement", "question": qa["question"], "error": str(exc)})

        if i % args.save_every == 0:
            pd.DataFrame(rows).to_csv(OUT_DATA / "per_query_partial.csv", index=False)
            print(f"[Fix05] {i}/{len(qa_use)} queries rows={len(rows)}", flush=True)
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ok = df[df["error"].fillna("").eq("")].copy() if "error" in df.columns else df.copy()
    summary = ok.groupby(["condition", "n_noise", "noise_rate"], dropna=False).agg(
        n=("question", "count"),
        faith=("faithfulness_score", "mean"),
        halluc=("is_hallucination", "mean"),
        sim=("mean_retrieval_similarity", "mean"),
    ).reset_index()
    for col in ["faith", "halluc", "sim"]:
        summary[col] = summary[col].round(6)

    base = float(ok[ok["condition"] == "baseline"]["faithfulness_score"].mean())
    rows = []
    for cond in ["random_noise", "coherent_uninformative_noise"]:
        sub = summary[summary["condition"] == cond].dropna(subset=["noise_rate"])
        if len(sub) >= 2:
            slope = float(np.polyfit(sub["noise_rate"], sub["faith"], 1)[0])
            sim_slope = float(np.polyfit(sub["noise_rate"], sub["sim"], 1)[0])
            rows.append({
                "condition": cond,
                "faith_slope_per_noise_rate": round(slope, 6),
                "sim_slope_per_noise_rate": round(sim_slope, 6),
                "drop_at_full_noise": round(base - float(sub.sort_values("noise_rate")["faith"].iloc[-1]), 6),
            })
    if (ok["condition"] == "hcpc_v1_refinement").any():
        rows.append({
            "condition": "hcpc_v1_refinement",
            "faith_slope_per_noise_rate": np.nan,
            "sim_slope_per_noise_rate": np.nan,
            "drop_at_full_noise": round(base - float(ok[ok["condition"] == "hcpc_v1_refinement"]["faithfulness_score"].mean()), 6),
        })
    return summary, pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_contexts", type=int, default=300)
    parser.add_argument("--backend", choices=["ollama", "together", "groq"], default="ollama")
    parser.add_argument("--model", default="mistral")
    parser.add_argument("--n_noise", nargs="+", type=int, default=[1, 2, 3])
    parser.add_argument("--save_every", type=int, default=25)
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS)
    df = run(args)
    df.to_csv(OUT_DATA / "per_query.csv", index=False)
    summary, slopes = summarize(df)
    summary.to_csv(OUT_RESULTS / "noise_summary.csv", index=False)
    slopes.to_csv(OUT_RESULTS / "slope_response.csv", index=False)
    write_markdown_table(
        OUT_RESULTS / "summary.md",
        "Fix 5 - coherence-preserving noise",
        {"Summary": summary, "Slope Response": slopes},
    )


if __name__ == "__main__":
    main()
