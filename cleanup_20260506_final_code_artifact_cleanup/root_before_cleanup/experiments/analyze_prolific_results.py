"""
analyze_prolific_results.py — Item A2 analysis pass
====================================================

Consumes the raw Prolific export and the sample manifest produced by
`prepare_prolific_study.py`, computes inter-annotator agreement (Fleiss'
kappa), and reports the human-vs-NLI correlations needed for the §6.X
"Human Validation" subsection.

Inputs (in --study_dir):
    raw_annotations.csv  — Prolific export, schema:
        task_id, annotator_id, faithful_yn, correctness_1to5,
        helpfulness_1to5, comment
    sample_manifest.csv  — written by prepare_prolific_study.py

Outputs (in --study_dir):
    aggregated_annotations.csv — per-task: majority labels + means
    agreement_report.md        — Fleiss' kappa, %-agreement
    nli_correlation.csv        — Spearman / Pearson for NLI vs human
    coherence_paradox_human.csv — per-condition: human-faithfulness rate
    summary.md                 — human-readable digest for the paper
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import os
from typing import Dict, List

import numpy as np
import pandas as pd

DEFAULT_DIR = "results/human_validation/study_v1"


# ── Fleiss' kappa ────────────────────────────────────────────────────────────

def fleiss_kappa(table: np.ndarray) -> float:
    """
    Fleiss' kappa for N items × k categories. table[i, j] = number of
    annotators who assigned item i to category j.
    """
    n_items, n_cat = table.shape
    n_raters = table.sum(axis=1).max()
    if n_raters < 2:
        return float("nan")

    # P_i: agreement among raters for item i
    P_i = ((table ** 2).sum(axis=1) - n_raters) / (n_raters * (n_raters - 1))
    P_bar = P_i.mean()

    # P_e: chance agreement
    p_j = table.sum(axis=0) / (n_items * n_raters)
    P_e = (p_j ** 2).sum()

    if P_e == 1:
        return 1.0
    return float((P_bar - P_e) / (1 - P_e))


def _binary_kappa(annotations: pd.DataFrame, label_col: str) -> float:
    """Fleiss' kappa for a YES/NO label column."""
    grouped = annotations.groupby("task_id")[label_col].apply(list)
    rows = []
    for _, labels in grouped.items():
        yes = sum(1 for v in labels if str(v).strip().upper() in ("YES", "Y", "TRUE", "1"))
        no  = len(labels) - yes
        rows.append([yes, no])
    return fleiss_kappa(np.asarray(rows, dtype=float))


def _ordinal_kappa(annotations: pd.DataFrame, label_col: str, levels: int = 5) -> float:
    """Fleiss' kappa for an ordinal 1..N column."""
    grouped = annotations.groupby("task_id")[label_col].apply(list)
    rows = []
    for _, labels in grouped.items():
        counts = [0] * levels
        for v in labels:
            try:
                lv = int(round(float(v)))
                if 1 <= lv <= levels:
                    counts[lv - 1] += 1
            except (TypeError, ValueError):
                continue
        rows.append(counts)
    return fleiss_kappa(np.asarray(rows, dtype=float))


# ── Aggregation ──────────────────────────────────────────────────────────────

def aggregate_annotations(annotations: pd.DataFrame) -> pd.DataFrame:
    """One row per task with majority binary label and mean ordinal scores."""
    grouped = annotations.groupby("task_id")
    rows = []
    for tid, sub in grouped:
        binary_yes = sum(
            1 for v in sub["faithful_yn"]
            if str(v).strip().upper() in ("YES", "Y", "TRUE", "1")
        )
        rows.append({
            "task_id":            tid,
            "n_annotations":      len(sub),
            "human_faithful_rate": binary_yes / len(sub),
            "majority_faithful":   binary_yes >= (len(sub) - binary_yes),
            "mean_correctness":    pd.to_numeric(sub.get("correctness_1to5"), errors="coerce").mean(),
            "mean_helpfulness":    pd.to_numeric(sub.get("helpfulness_1to5"), errors="coerce").mean(),
            "any_disagreement":    binary_yes not in (0, len(sub)),
        })
    return pd.DataFrame(rows)


# ── NLI correlation ──────────────────────────────────────────────────────────

def nli_correlation(merged: pd.DataFrame) -> pd.DataFrame:
    from scipy.stats import spearmanr, pearsonr
    rows = []
    pairs = [
        ("nli_faithfulness", "human_faithful_rate"),
        ("nli_faithfulness", "mean_correctness"),
        ("nli_faithfulness", "mean_helpfulness"),
    ]
    for x_col, y_col in pairs:
        sub = merged[[x_col, y_col]].dropna()
        if len(sub) < 4:
            continue
        rho, prho = spearmanr(sub[x_col], sub[y_col])
        r, pr   = pearsonr(sub[x_col], sub[y_col])
        rows.append({
            "x":           x_col,
            "y":           y_col,
            "n":           len(sub),
            "spearman":    round(float(rho), 4),
            "spearman_p":  round(float(prho), 4),
            "pearson":     round(float(r), 4),
            "pearson_p":   round(float(pr), 4),
        })
    return pd.DataFrame(rows)


# ── Per-condition summary ────────────────────────────────────────────────────

def per_condition_summary(merged: pd.DataFrame) -> pd.DataFrame:
    grouped = merged.groupby("condition")
    rows = []
    for cond, sub in grouped:
        rows.append({
            "condition":              cond,
            "n":                      len(sub),
            "human_faith_rate":       round(float(sub["human_faithful_rate"].mean()), 4),
            "majority_faithful_rate": round(float(sub["majority_faithful"].mean()), 4),
            "nli_faith_rate":         round(float((sub["nli_faithfulness"] >= 0.5).mean()), 4),
            "mean_correctness":       round(float(sub["mean_correctness"].mean()), 4),
            "mean_helpfulness":       round(float(sub["mean_helpfulness"].mean()), 4),
        })
    return pd.DataFrame(rows)


def write_summary_md(
    kappa: Dict[str, float],
    corr: pd.DataFrame,
    cond: pd.DataFrame,
    out_path: str,
) -> None:
    lines = [
        "# Human Validation — Summary",
        "",
        "## Inter-annotator agreement (Fleiss' kappa)",
        "",
        f"- faithful (binary): **{kappa.get('faithful', float('nan')):.3f}**",
        f"- correctness (1-5): **{kappa.get('correctness', float('nan')):.3f}**",
        f"- helpfulness (1-5): **{kappa.get('helpfulness', float('nan')):.3f}**",
        "",
        "Conventional reference values: < 0.20 poor, 0.21–0.40 fair, "
        "0.41–0.60 moderate, 0.61–0.80 substantial, > 0.81 almost perfect.",
        "",
        "## NLI vs human correlations",
        "",
        corr.to_markdown(index=False) if not corr.empty else "(insufficient data)",
        "",
        "## Per-condition human-faithfulness",
        "",
        cond.to_markdown(index=False) if not cond.empty else "(no data)",
        "",
        "Coherence-paradox check: `condition='hcpc_v1'` should show a lower "
        "human_faith_rate than `condition='baseline'`. If it does, the paradox "
        "survives human evaluation.",
    ]
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--study_dir", default=DEFAULT_DIR)
    args = parser.parse_args()

    raw_path = os.path.join(args.study_dir, "raw_annotations.csv")
    man_path = os.path.join(args.study_dir, "sample_manifest.csv")
    if not os.path.exists(raw_path) or not os.path.exists(man_path):
        raise FileNotFoundError(
            "Required inputs not found. Expected:\n"
            f"  {raw_path}\n  {man_path}\n"
            "Run experiments/prepare_prolific_study.py and import the Prolific "
            "export as raw_annotations.csv first."
        )

    raw = pd.read_csv(raw_path)
    manifest = pd.read_csv(man_path)

    aggregated = aggregate_annotations(raw)
    aggregated.to_csv(os.path.join(args.study_dir, "aggregated_annotations.csv"), index=False)

    merged = aggregated.merge(manifest, on="task_id", how="inner")

    kappa = {
        "faithful":    _binary_kappa(raw,    "faithful_yn"),
        "correctness": _ordinal_kappa(raw,   "correctness_1to5", levels=5),
        "helpfulness": _ordinal_kappa(raw,   "helpfulness_1to5", levels=5),
    }
    with open(os.path.join(args.study_dir, "agreement_report.md"), "w") as fh:
        for k, v in kappa.items():
            fh.write(f"- {k}: {v:.4f}\n")

    corr = nli_correlation(merged)
    corr.to_csv(os.path.join(args.study_dir, "nli_correlation.csv"), index=False)

    cond = per_condition_summary(merged)
    cond.to_csv(os.path.join(args.study_dir, "coherence_paradox_human.csv"), index=False)

    write_summary_md(kappa, corr, cond, os.path.join(args.study_dir, "summary.md"))
    print(f"[HumanEval] outputs -> {args.study_dir}/")


if __name__ == "__main__":
    main()
