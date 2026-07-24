"""
Fix 7: independent Together.ai Llama-3.3-70B reproduction.

Runs the SQuAD 70B paradox cell on Together.ai and compares against the
previous frontier-scale reference magnitude. The claim stands only if
magnitudes match within the preregistered +/-0.02 tolerance.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

from experiments.revision_utils import ensure_dirs, make_llm, write_markdown_table
from src.dataset_loaders import load_dataset_by_name
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.rag_pipeline import RAGPipeline


OUT_DATA = Path("data/revision/fix_07")
OUT_RESULTS = Path("results/revision/fix_07")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_contexts", type=int, default=200)
    parser.add_argument("--model", default="meta-llama/Llama-3.3-70B-Instruct-Turbo")
    parser.add_argument("--reference_magnitude", type=float, default=0.100)
    parser.add_argument("--groq_reference", type=float, dest="reference_magnitude",
                        help="Deprecated alias for --reference_magnitude.")
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS)
    docs, qa_pairs = load_dataset_by_name("squad", max_papers=args.max_contexts)
    rng = random.Random(args.seed)
    qa = list(qa_pairs)
    rng.shuffle(qa)
    qa = qa[: min(args.n, len(qa))]
    pipe = RAGPipeline(
        chunk_size=1024,
        chunk_overlap=100,
        top_k=3,
        model_name=args.model,
        persist_dir="./chroma_db_fix07/squad",
    )
    pipe.index_documents(docs, collection_name="fix07_squad")
    pipe.llm = make_llm("together", args.model, temperature=0.0)
    v1 = HCPCRetriever(pipe, sim_threshold=0.50, ce_threshold=0.00, top_k=3)
    detector = HallucinationDetector()
    rows: List[Dict[str, Any]] = []
    for item in qa:
        for condition, retriever in [("baseline", None), ("hcpc_v1", v1)]:
            if retriever is None:
                docs_set, _ = pipe.retrieve_with_scores(item["question"])
            else:
                docs_set, _ = retriever.retrieve(item["question"])
            gen = pipe.generate(item["question"], docs_set)
            nli = detector.detect(gen["answer"], gen["context"])
            rows.append({
                "dataset": "squad",
                "model": args.model,
                "backend": "together",
                "condition": condition,
                "question": item["question"],
                "ground_truth": item.get("ground_truth", ""),
                "answer": gen["answer"],
                "faithfulness_score": float(nli["faithfulness_score"]),
                "is_hallucination": bool(nli["is_hallucination"]),
            })
        pd.DataFrame(rows).to_csv(OUT_DATA / "per_query.csv", index=False)

    df = pd.DataFrame(rows)
    summary = df.groupby("condition").agg(
        n=("question", "count"),
        faithfulness=("faithfulness_score", "mean"),
        hallucination_rate=("is_hallucination", "mean"),
    ).reset_index()
    base = float(summary[summary["condition"] == "baseline"]["faithfulness"].iloc[0])
    v1faith = float(summary[summary["condition"] == "hcpc_v1"]["faithfulness"].iloc[0])
    magnitude = base - v1faith
    compare = pd.DataFrame([{
        "together_magnitude": round(magnitude, 6),
        "reference_magnitude": args.reference_magnitude,
        "abs_difference": round(abs(magnitude - args.reference_magnitude), 6),
        "matches_within_0p02": bool(abs(magnitude - args.reference_magnitude) <= 0.02),
        "suspicious_exact_match": bool(round(magnitude, 6) == round(args.reference_magnitude, 6)),
    }])
    summary.to_csv(OUT_RESULTS / "together_summary.csv", index=False)
    compare.to_csv(OUT_RESULTS / "together_reference_comparison.csv", index=False)
    write_markdown_table(OUT_RESULTS / "summary.md", "Fix 7 - Together 70B reproduction", {"Summary": summary, "Comparison": compare})


if __name__ == "__main__":
    main()
