"""
Fix 2: scaled headline-cell rigor upgrade.

Runs SQuAD/Mistral-7B at n=500 with five seeds across:
    baseline, HCPC-v1, HCPC-v2

Reports 10000-resample bootstrap CIs for continuous metrics and Wilson score
CIs for hallucination rate.  This replaces the old n=30 Table 1 cell.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from experiments.revision_utils import (
    bootstrap_mean_ci,
    cohens_d,
    ensure_dirs,
    make_llm,
    wilson_ci,
    write_markdown_table,
)
from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.rag_pipeline import RAGPipeline
from src.retrieval_metrics import compute_retrieval_quality


OUT_DATA = Path("data/revision/fix_02")
OUT_RESULTS = Path("results/revision/fix_02")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
V1_SIM, V1_CE = 0.50, 0.00
V2_SIM, V2_CE = 0.45, -0.20


def tagged_path(path: Path, tag: str) -> Path:
    """Return `foo_tag.csv` for worker shards, or `foo.csv` for final runs."""
    clean = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in tag.strip())
    if not clean:
        return path
    return path.with_name(f"{path.stem}_{clean}{path.suffix}")


def build_pipeline(dataset: str, model: str, seed: int, max_contexts: int,
                   backend: str) -> tuple[RAGPipeline, list[dict]]:
    docs, qa_pairs = load_dataset_by_name(dataset, max_papers=max_contexts)
    if not docs or not qa_pairs:
        raise RuntimeError(f"{dataset}: no docs/QA pairs loaded")
    coll = f"fix02_{dataset}_{model.replace('/', '_')}_s{seed}"[:63]
    pipe = RAGPipeline(
        chunk_size=1024,
        chunk_overlap=100,
        top_k=3,
        model_name=model,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_fix02/{coll}",
    )
    pipe.index_documents(docs, collection_name=coll)
    pipe.llm = make_llm(backend, model, temperature=0.0)
    return pipe, qa_pairs


def evaluate_condition(pipe: RAGPipeline, detector: HallucinationDetector,
                       qa: dict, condition: str, retriever: Any) -> Dict[str, Any]:
    if retriever is None:
        docs, _ = pipe.retrieve_with_scores(qa["question"])
        log: Dict[str, Any] = {}
    else:
        out = retriever.retrieve(qa["question"])
        docs, log = out if isinstance(out, tuple) else (out, {})

    t0 = time.time()
    gen = pipe.generate(qa["question"], docs)
    latency = time.time() - t0
    nli = detector.detect(gen["answer"], gen["context"])
    rm = compute_retrieval_quality(qa["question"], docs, pipe.embeddings)
    return {
        "question": qa["question"],
        "ground_truth": qa.get("ground_truth", ""),
        "condition": condition,
        "answer": gen["answer"],
        "context": gen["context"],
        "faithfulness_score": float(nli["faithfulness_score"]),
        "is_hallucination": bool(nli["is_hallucination"]),
        "mean_retrieval_similarity": float(rm.get("mean_similarity", 0.0)),
        "refined": bool(log.get("refined", False)) if isinstance(log, dict) else False,
        "ccs": float(log.get("context_coherence", -1.0)) if isinstance(log, dict) else -1.0,
        "latency_s": round(float(latency), 3),
    }


def run_seed(args: argparse.Namespace, dataset: str, seed: int,
             detector: HallucinationDetector) -> List[Dict[str, Any]]:
    print(f"[Fix02] dataset={dataset} seed={seed} n={args.n} model={args.model}")
    pipe, qa_pairs = build_pipeline(dataset, args.model, seed, args.max_contexts, args.backend)
    rng = random.Random(seed)
    qa_use = list(qa_pairs)
    rng.shuffle(qa_use)
    qa_use = qa_use[: min(args.n, len(qa_use))]

    v1 = HCPCRetriever(
        pipeline=pipe,
        sim_threshold=V1_SIM,
        ce_threshold=V1_CE,
        top_k=3,
    )
    v2 = HCPCv2Retriever(
        pipeline=pipe,
        sim_threshold=V2_SIM,
        ce_threshold=V2_CE,
        top_k_protected=2,
        max_refine=2,
    )
    conditions = [
        ("baseline", None),
        ("hcpc_v1", v1),
        ("hcpc_v2", v2),
    ]

    rows: List[Dict[str, Any]] = []
    completed_items: set[tuple[str, str]] = set()
    partial_path = tagged_path(OUT_DATA / f"{dataset}_seed{seed}_partial.csv", args.output_tag)
    if args.resume_partial and partial_path.exists() and partial_path.stat().st_size > 0:
        partial = pd.read_csv(partial_path)
        if not partial.empty:
            rows = partial.to_dict("records")
            partial_for_resume = partial.copy()
            partial_for_resume["_resume_question"] = partial_for_resume["question"].fillna("").astype(str)
            if "ground_truth" in partial_for_resume.columns:
                partial_for_resume["_resume_ground_truth"] = (
                    partial_for_resume["ground_truth"].fillna("").astype(str)
                )
            else:
                partial_for_resume["_resume_ground_truth"] = ""
            complete = (
                partial_for_resume.groupby(["_resume_question", "_resume_ground_truth"])["condition"]
                .nunique()
                .loc[lambda s: s >= len(conditions)]
            )
            completed_items = set(complete.index)
            print(
                f"[Fix02] resumed {dataset}/seed{seed}: "
                f"{len(completed_items)}/{len(qa_use)} complete queries from {partial_path}"
            )

    for i, qa in enumerate(qa_use, start=1):
        qa_identity = (str(qa.get("question", "")), str(qa.get("ground_truth", "")))
        if qa_identity in completed_items:
            continue
        for label, retriever in conditions:
            try:
                row = evaluate_condition(pipe, detector, qa, label, retriever)
                row.update({
                    "dataset": dataset,
                    "seed": seed,
                    "model": args.model,
                    "backend": args.backend,
                })
                rows.append(row)
            except Exception as exc:
                rows.append({
                    "dataset": dataset,
                    "seed": seed,
                    "model": args.model,
                    "backend": args.backend,
                    "question": qa.get("question", ""),
                    "ground_truth": qa.get("ground_truth", ""),
                    "condition": label,
                    "error": f"{type(exc).__name__}:{exc}",
                })
        if i == 1 or i % args.save_every == 0 or i == len(qa_use):
            pd.DataFrame(rows).to_csv(
                partial_path,
                index=False,
            )
            print(f"[Fix02] {dataset}/seed{seed}: {i}/{len(qa_use)} queries")
    return rows


def aggregate(df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    ok = df[df["error"].fillna("").eq("")].copy() if "error" in df.columns else df.copy()
    summary_rows: List[Dict[str, Any]] = []
    for (dataset, condition), sub in ok.groupby(["dataset", "condition"]):
        n = len(sub)
        faith, faith_lo, faith_hi = bootstrap_mean_ci(sub["faithfulness_score"], seed=seed)
        sim, sim_lo, sim_hi = bootstrap_mean_ci(sub["mean_retrieval_similarity"], seed=seed)
        refine, refine_lo, refine_hi = bootstrap_mean_ci(sub["refined"].astype(float), seed=seed)
        halluc, halluc_lo, halluc_hi = wilson_ci(int(sub["is_hallucination"].sum()), n)
        summary_rows.append({
            "dataset": dataset,
            "condition": condition,
            "n_rows": n,
            "faithfulness": round(faith, 6),
            "faith_ci95_lo": round(faith_lo, 6),
            "faith_ci95_hi": round(faith_hi, 6),
            "hallucination_rate": round(halluc, 6),
            "halluc_wilson95_lo": round(halluc_lo, 6),
            "halluc_wilson95_hi": round(halluc_hi, 6),
            "retrieval_similarity": round(sim, 6),
            "sim_ci95_lo": round(sim_lo, 6),
            "sim_ci95_hi": round(sim_hi, 6),
            "refine_rate": round(refine, 6),
            "refine_ci95_lo": round(refine_lo, 6),
            "refine_ci95_hi": round(refine_hi, 6),
        })

    contrast_rows: List[Dict[str, Any]] = []
    for (dataset, seed_id), sub in ok.groupby(["dataset", "seed"]):
        piv = sub.pivot_table(
            index="question",
            columns="condition",
            values="faithfulness_score",
            aggfunc="first",
        ).dropna()
        for a, b, label, alt in [
            ("baseline", "hcpc_v1", "baseline_minus_v1", "greater"),
            ("hcpc_v2", "hcpc_v1", "v2_minus_v1", "greater"),
            ("baseline", "hcpc_v2", "baseline_minus_v2", "two-sided"),
        ]:
            if a not in piv or b not in piv or len(piv) < 5:
                continue
            diff = piv[a].values - piv[b].values
            try:
                stat, p = wilcoxon(diff, alternative=alt)
            except ValueError:
                stat, p = float("nan"), float("nan")
            pt, lo, hi = bootstrap_mean_ci(diff, seed=seed_id)
            contrast_rows.append({
                "dataset": dataset,
                "seed": int(seed_id),
                "contrast": label,
                "n_pairs": int(len(diff)),
                "mean_diff": round(pt, 6),
                "boot_ci95_lo": round(lo, 6),
                "boot_ci95_hi": round(hi, 6),
                "wilcoxon_stat": None if not np.isfinite(stat) else round(float(stat), 6),
                "wilcoxon_p": None if not np.isfinite(p) else float(p),
                "cohens_dz": round(cohens_d(diff), 6),
            })
    return pd.DataFrame(summary_rows), pd.DataFrame(contrast_rows)


def write_columns() -> None:
    text = """# Fix 2 column documentation

## `per_query.csv`

One row per `(dataset, seed, query, condition)`. Important columns:

- `faithfulness_score`: DeBERTa-v3 NLI entailment score.
- `is_hallucination`: `faithfulness_score < 0.5`.
- `mean_retrieval_similarity`: query-to-context retrieval similarity.
- `refined`: whether HCPC/HCPC-v2 changed the context.
- `context`: generated-context text, retained for Fix 3 multi-metric scoring.

## `headline_table.csv`

Aggregated pooled rows with bootstrap 95% CIs for continuous metrics and
Wilson score CIs for hallucination rate.
"""
    (OUT_DATA / "COLUMNS.md").write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["squad"])
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--seeds", nargs="+", type=int, default=[41, 42, 43, 44, 45])
    parser.add_argument("--backend", choices=["ollama", "together", "groq"], default="ollama")
    parser.add_argument("--model", default="mistral")
    parser.add_argument("--max_contexts", type=int, default=600)
    parser.add_argument("--save_every", type=int, default=25)
    parser.add_argument(
        "--output_tag",
        default="",
        help="Optional shard tag; writes per_query_<tag>.csv and summary_<tag>.md.",
    )
    parser.add_argument(
        "--resume_partial",
        action="store_true",
        help="Resume from the tagged per-seed partial CSV when it exists.",
    )
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS)
    write_columns()
    per_query_path = tagged_path(OUT_DATA / "per_query.csv", args.output_tag)
    headline_path = tagged_path(OUT_RESULTS / "headline_table.csv", args.output_tag)
    contrast_path = tagged_path(OUT_RESULTS / "paired_contrasts.csv", args.output_tag)
    summary_path = tagged_path(OUT_RESULTS / "summary.md", args.output_tag)

    detector = HallucinationDetector()
    all_rows: List[Dict[str, Any]] = []
    for dataset in args.datasets:
        if dataset not in DATASET_REGISTRY:
            print(f"[Fix02] unknown dataset {dataset}; skipping")
            continue
        for seed in args.seeds:
            rows = run_seed(args, dataset, seed, detector)
            all_rows.extend(rows)
            pd.DataFrame(all_rows).to_csv(per_query_path, index=False)

    df = pd.DataFrame(all_rows)
    df.to_csv(per_query_path, index=False)
    summary, contrasts = aggregate(df)
    summary.to_csv(headline_path, index=False)
    contrasts.to_csv(contrast_path, index=False)
    write_markdown_table(
        summary_path,
        "Fix 2 - scaled headline n=500 x 5 seeds",
        {"Headline Table": summary, "Paired Contrasts": contrasts},
    )
    print(f"[Fix02] wrote {len(df)} rows to {per_query_path}")


if __name__ == "__main__":
    main()
