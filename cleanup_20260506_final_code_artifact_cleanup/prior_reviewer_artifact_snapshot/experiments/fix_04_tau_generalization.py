"""
Fix 4: cross-dataset tau generalization.

Tunes the CCS-gate threshold tau on one dataset and evaluates recovery on all
datasets, producing a 5x5 tune-on/eval-on matrix.  This directly tests whether
the policy depends on SQuAD-specific threshold tuning.
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

from experiments.revision_utils import ensure_dirs, make_llm, write_markdown_table
from src.ccs_gate_retriever import CCSGateRetriever
from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.rag_pipeline import RAGPipeline


OUT_DATA = Path("data/revision/fix_04")
OUT_RESULTS = Path("results/revision/fix_04")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def run_dataset_tau(args: argparse.Namespace, dataset: str, tau: float,
                    detector: HallucinationDetector) -> List[Dict[str, Any]]:
    docs, qa_pairs = load_dataset_by_name(dataset, max_papers=args.max_contexts)
    if not docs or not qa_pairs:
        return []
    rng = random.Random(args.seed)
    qa_use = list(qa_pairs)
    rng.shuffle(qa_use)
    qa_use = qa_use[: min(args.n, len(qa_use))]

    coll = f"fix04_{dataset}_tau{str(tau).replace('.', 'p')}"[:63]
    pipe = RAGPipeline(
        chunk_size=1024,
        chunk_overlap=100,
        top_k=3,
        model_name=args.model,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_fix04/{coll}",
    )
    pipe.index_documents(docs, collection_name=coll)
    pipe.llm = make_llm(args.backend, args.model, temperature=0.0)
    v1 = HCPCRetriever(pipeline=pipe, sim_threshold=0.50, ce_threshold=0.00, top_k=3)
    gate = CCSGateRetriever(pipeline=pipe, ccs_threshold=tau, top_k=3, fallback="hcpc_v1")

    conditions = [("baseline", None), ("hcpc_v1", v1), ("ccs_gate", gate)]
    partial_path = OUT_DATA / f"{dataset}_tau{tau}_partial.csv"
    rows: List[Dict[str, Any]] = []
    completed_count = 0
    if args.resume_partial and partial_path.exists() and partial_path.stat().st_size > 0:
        partial = pd.read_csv(partial_path)
        if not partial.empty:
            rows = partial.to_dict("records")
            completed_count = min(len(partial) // len(conditions), len(qa_use))
            print(
                f"[Fix04] resumed {dataset} tau={tau}: "
                f"{completed_count}/{len(qa_use)} queries from {partial_path}"
            )
            if completed_count >= len(qa_use):
                return rows

    for i, qa in enumerate(qa_use, start=1):
        if i <= completed_count:
            continue
        for condition, retriever in conditions:
            try:
                if retriever is None:
                    docs_set, _ = pipe.retrieve_with_scores(qa["question"])
                    log: Dict[str, Any] = {"gate_fired": False}
                else:
                    docs_set, log = retriever.retrieve(qa["question"])
                gen = pipe.generate(qa["question"], docs_set)
                nli = detector.detect(gen["answer"], gen["context"])
                rows.append({
                    "dataset": dataset,
                    "tau": tau,
                    "condition": condition,
                    "question": qa["question"],
                    "ground_truth": qa.get("ground_truth", ""),
                    "faithfulness_score": float(nli["faithfulness_score"]),
                    "is_hallucination": bool(nli["is_hallucination"]),
                    "gate_fired": bool(log.get("gate_fired", False)) if isinstance(log, dict) else False,
                    "ccs_pre": float(log.get("ccs_pre", -1.0)) if isinstance(log, dict) else -1.0,
                })
            except Exception as exc:
                rows.append({
                    "dataset": dataset,
                    "tau": tau,
                    "condition": condition,
                    "question": qa.get("question", ""),
                    "error": f"{type(exc).__name__}:{exc}",
                })
        if i == 1 or i % args.save_every == 0 or i == len(qa_use):
            pd.DataFrame(rows).to_csv(partial_path, index=False)
            print(f"[Fix04] {dataset} tau={tau}: {i}/{len(qa_use)} queries rows={len(rows)}")
    return rows


def summarize_tau(df: pd.DataFrame) -> pd.DataFrame:
    ok = df[df["error"].fillna("").eq("")].copy() if "error" in df.columns else df.copy()
    means = ok.groupby(["dataset", "tau", "condition"])["faithfulness_score"].mean().reset_index()
    rows: List[Dict[str, Any]] = []
    for (dataset, tau), sub in means.groupby(["dataset", "tau"]):
        vals = dict(zip(sub["condition"], sub["faithfulness_score"]))
        base = vals.get("baseline", np.nan)
        v1 = vals.get("hcpc_v1", np.nan)
        gate = vals.get("ccs_gate", np.nan)
        denom = base - v1
        recovery = (gate - v1) / denom if np.isfinite(denom) and abs(denom) > 1e-9 else np.nan
        rows.append({
            "dataset": dataset,
            "tau": tau,
            "faith_baseline": round(float(base), 6) if np.isfinite(base) else np.nan,
            "faith_hcpc_v1": round(float(v1), 6) if np.isfinite(v1) else np.nan,
            "faith_ccs_gate": round(float(gate), 6) if np.isfinite(gate) else np.nan,
            "recovery": round(float(recovery), 6) if np.isfinite(recovery) else np.nan,
        })
    return pd.DataFrame(rows)


def build_matrix(summary: pd.DataFrame, datasets: list[str]) -> pd.DataFrame:
    best_tau = (
        summary.sort_values("recovery", ascending=False)
        .dropna(subset=["recovery"])
        .groupby("dataset")
        .head(1)[["dataset", "tau"]]
        .rename(columns={"dataset": "tune_dataset"})
    )
    rows: List[Dict[str, Any]] = []
    for _, tuned in best_tau.iterrows():
        tune_ds = tuned["tune_dataset"]
        tau = float(tuned["tau"])
        rec: Dict[str, Any] = {"tune_dataset": tune_ds, "tau": tau}
        for eval_ds in datasets:
            hit = summary[(summary["dataset"] == eval_ds) & (summary["tau"] == tau)]
            rec[eval_ds] = float(hit["recovery"].iloc[0]) if len(hit) else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa", "hotpotqa", "naturalqs", "triviaqa"])
    parser.add_argument("--taus", nargs="+", type=float, default=[0.30, 0.40, 0.50, 0.60, 0.70])
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_contexts", type=int, default=150)
    parser.add_argument("--backend", choices=["ollama", "together", "groq"], default="ollama")
    parser.add_argument("--model", default="mistral")
    parser.add_argument("--save_every", type=int, default=25)
    parser.add_argument("--resume_partial", action="store_true")
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS)
    detector = HallucinationDetector()
    all_rows: List[Dict[str, Any]] = []
    for dataset in args.datasets:
        if dataset not in DATASET_REGISTRY:
            continue
        for tau in args.taus:
            print(f"[Fix04] dataset={dataset} tau={tau}")
            all_rows.extend(run_dataset_tau(args, dataset, tau, detector))
            pd.DataFrame(all_rows).to_csv(OUT_DATA / "per_query.csv", index=False)

    df = pd.DataFrame(all_rows)
    df.to_csv(OUT_DATA / "per_query.csv", index=False)
    tau_summary = summarize_tau(df)
    matrix = build_matrix(tau_summary, args.datasets)
    tau_summary.to_csv(OUT_RESULTS / "tau_summary.csv", index=False)
    matrix.to_csv(OUT_RESULTS / "tau_transfer_matrix.csv", index=False)

    # Diagonal vs off-diagonal flag.
    flags = []
    for _, row in matrix.iterrows():
        tune = row["tune_dataset"]
        diag = row.get(tune, np.nan)
        off = [row[d] for d in args.datasets if d != tune and pd.notna(row.get(d, np.nan))]
        off_mean = float(np.mean(off)) if off else np.nan
        flags.append({
            "tune_dataset": tune,
            "diag_recovery": diag,
            "offdiag_mean_recovery": off_mean,
            "diag_minus_offdiag": diag - off_mean if pd.notna(diag) and pd.notna(off_mean) else np.nan,
            "must_flag_in_section8": bool(pd.notna(diag) and pd.notna(off_mean) and (diag - off_mean) > 0.03),
        })
    flag_df = pd.DataFrame(flags)
    flag_df.to_csv(OUT_RESULTS / "generalization_flags.csv", index=False)
    write_markdown_table(
        OUT_RESULTS / "summary.md",
        "Fix 4 - tau generalization",
        {"Tau Summary": tau_summary, "Transfer Matrix": matrix, "Flags": flag_df},
    )


if __name__ == "__main__":
    main()
