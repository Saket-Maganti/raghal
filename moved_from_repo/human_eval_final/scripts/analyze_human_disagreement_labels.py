#!/usr/bin/env python3
"""Analyze labels for the targeted scorer-disagreement annotation batch."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


SCORERS = {
    "DeBERTa": "deberta_score",
    "second_NLI": "second_nli_score",
    "RAGAS_style": "ragas_style_score",
}


def label_to_binary(value: object) -> float:
    text = str(value).strip().lower()
    if text in {"faithful", "supported", "1", "true", "yes"}:
        return 1.0
    if text in {"hallucinated", "unsupported", "0", "false", "no"}:
        return 0.0
    return np.nan


def cohens_kappa(a: np.ndarray, b: np.ndarray) -> float:
    mask = np.isfinite(a) & np.isfinite(b)
    a = a[mask].astype(int)
    b = b[mask].astype(int)
    if a.size == 0:
        return np.nan
    po = float((a == b).mean())
    pa = float(a.mean())
    pb = float(b.mean())
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1.0 else float((po - pe) / (1 - pe))


def auroc(y_true: np.ndarray, score: np.ndarray) -> float:
    mask = np.isfinite(y_true) & np.isfinite(score)
    y = y_true[mask].astype(int)
    s = score[mask].astype(float)
    n_pos = int(y.sum())
    n_neg = int((1 - y).sum())
    if n_pos == 0 or n_neg == 0:
        return np.nan
    ranks = pd.Series(s).rank(method="average").to_numpy()
    rank_sum_pos = ranks[y == 1].sum()
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def auprc(y_true: np.ndarray, score: np.ndarray) -> float:
    mask = np.isfinite(y_true) & np.isfinite(score)
    y = y_true[mask].astype(int)
    s = score[mask].astype(float)
    n_pos = int(y.sum())
    if n_pos == 0:
        return np.nan
    order = np.argsort(-s)
    y_sorted = y[order]
    tp = np.cumsum(y_sorted)
    precision = tp / (np.arange(y_sorted.size) + 1)
    return float((precision * y_sorted).sum() / n_pos)


def balanced_accuracy(y_true: np.ndarray, score: np.ndarray, threshold: float = 0.5) -> float:
    mask = np.isfinite(y_true) & np.isfinite(score)
    y = y_true[mask].astype(int)
    pred = (score[mask] >= threshold).astype(int)
    pos = y == 1
    neg = y == 0
    if pos.sum() == 0 or neg.sum() == 0:
        return np.nan
    tpr = float((pred[pos] == 1).mean())
    tnr = float((pred[neg] == 0).mean())
    return (tpr + tnr) / 2


def correlations(y_true: np.ndarray, score: np.ndarray) -> tuple[float, float]:
    mask = np.isfinite(y_true) & np.isfinite(score)
    y = pd.Series(y_true[mask])
    s = pd.Series(score[mask])
    if len(y) < 3 or y.nunique() < 2 or s.nunique() < 2:
        return np.nan, np.nan
    return float(y.corr(s, method="pearson")), float(y.corr(s, method="spearman"))


def bootstrap_ci(
    y_true: np.ndarray,
    score: np.ndarray,
    fn,
    n_bootstrap: int,
    seed: int,
) -> tuple[float, float]:
    mask = np.isfinite(y_true) & np.isfinite(score)
    y = y_true[mask]
    s = score[mask]
    if len(y) < 5:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, len(y), size=len(y))
        val = fn(y[idx], s[idx])
        if np.isfinite(val):
            vals.append(val)
    if not vals:
        return np.nan, np.nan
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return float(lo), float(hi)


def detect_rater_columns(df: pd.DataFrame) -> list[str]:
    candidates = []
    for col in df.columns:
        lower = col.lower()
        if "label" in lower and ("rater" in lower or "annotator" in lower):
            candidates.append(col)
    return candidates


def choose_reference_label(df: pd.DataFrame) -> tuple[str | None, np.ndarray]:
    for col in ["adjudicated_label", "majority_label", "reference_label", "annotator_label"]:
        if col in df.columns:
            vals = df[col].map(label_to_binary).to_numpy(dtype=float)
            if np.isfinite(vals).sum() > 0:
                return col, vals
    rater_cols = detect_rater_columns(df)
    if rater_cols:
        vals = df[rater_cols[0]].map(label_to_binary).to_numpy(dtype=float)
        if np.isfinite(vals).sum() > 0:
            return rater_cols[0], vals
    return None, np.array([], dtype=float)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="results/human_disagreement_expansion/annotation_batch_disagreement_100.csv",
    )
    parser.add_argument("--output", default=None)
    parser.add_argument("--n_bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    input_path = Path(args.input)
    df = pd.read_csv(input_path)
    
    # 1. Batch Composition
    composition = []
    if "condition" in df.columns:
        counts = df["condition"].value_counts().to_dict()
        for cond, count in counts.items():
            composition.append({"category": "condition", "name": cond, "count": count})
    if "disagreement_type" in df.columns:
        counts = df["disagreement_type"].value_counts().to_dict()
        for dtype, count in counts.items():
            composition.append({"category": "disagreement_type", "name": dtype, "count": count})
    
    comp_df = pd.DataFrame(composition)
    comp_path = input_path.with_name("batch_composition.csv")
    comp_df.to_csv(comp_path, index=False)
    print(f"Wrote batch composition to {comp_path}")

    # 2. Scorer Score Summary
    score_summaries = []
    for scorer_name, scorer_col in SCORERS.items():
        actual_col = None
        if scorer_col in df.columns:
            actual_col = scorer_col
        else:
            for alt in [f"{scorer_name.lower()}_score", f"local_{scorer_name.lower()}", f"{scorer_name.lower()}_hallucination_score"]:
                if alt in df.columns:
                    actual_col = alt
                    break
        
        if actual_col:
            score = pd.to_numeric(df[actual_col], errors="coerce")
            score_summaries.append({
                "scorer": scorer_name,
                "mean": score.mean(),
                "std": score.std(),
                "min": score.min(),
                "max": score.max(),
                "count": score.count()
            })
    
    score_sum_df = pd.DataFrame(score_summaries)
    score_sum_path = input_path.with_name("scorer_score_summary.csv")
    score_sum_df.to_csv(score_sum_path, index=False)
    print(f"Wrote scorer score summary to {score_sum_path}")

    # 3. Annotation Completeness Report
    missing_report = []
    missing_report.append("# Annotation Completeness Report\n\n")
    missing_report.append(f"Input file: `{input_path.name}`\n")
    missing_report.append(f"Total rows: {len(df)}\n\n")

    rater_cols = detect_rater_columns(df)
    adj_cols = [c for c in df.columns if "adjudicated" in c.lower()]
    all_annot_cols = rater_cols + adj_cols

    # Identify the load-bearing columns (rater1, rater2, adjudicated_label)
    load_bearing = [c for c in all_annot_cols
                    if c in ("human_label_rater1", "human_label_rater2",
                             "adjudicated_label", "adjudicated_confidence")]

    if not all_annot_cols:
        missing_report.append("No annotation columns detected.\n")
    else:
        missing_report.append("## Two-rater + adjudication completeness\n\n")
        missing_report.append("| Column | Filled Count | Missing Count | % Complete |\n")
        missing_report.append("| --- | --- | --- | --- |\n")
        for col in all_annot_cols:
            filled = df[col].notnull().sum()
            missing = len(df) - filled
            pct = (filled / len(df)) * 100
            missing_report.append(f"| `{col}` | {filled} | {missing} | {pct:.1f}% |\n")

    # Determine status:
    #  - if any load-bearing column has any NaN, status is INCOMPLETE
    #  - otherwise status is COMPLETE
    if not all_annot_cols:
        missing_report.append("\n**Status: No annotation columns found.**\n")
    elif load_bearing:
        any_missing = any(df[c].isnull().any() for c in load_bearing)
        if any_missing:
            missing_report.append(
                "\n**Status: INCOMPLETE.** One or more load-bearing "
                "columns (rater 1 / rater 2 / adjudicated) still contain "
                "missing values.\n"
            )
        else:
            n = len(df)
            disagreements = int((df["human_label_rater1"] != df["human_label_rater2"]).sum()) \
                if "human_label_rater1" in df.columns and "human_label_rater2" in df.columns else None
            if disagreements is not None:
                missing_report.append(
                    f"\n**Status: COMPLETE.** All {n} rows have rater 1, "
                    f"rater 2, and adjudicated labels. Of the {n} items, "
                    f"{disagreements} had rater-rater disagreement; "
                    "rater-rater disagreements are resolved in "
                    "`human_eval_adjudicated.csv` (column "
                    "`adjudication_notes`).\n"
                )
            else:
                missing_report.append(
                    f"\n**Status: COMPLETE.** All {n} rows have the "
                    "load-bearing annotation columns filled.\n"
                )
    else:
        missing_report.append("\n**Status: Some human labels are present.**\n")

    report_path = input_path.with_name("missing_human_labels_report.md")
    with open(report_path, "w") as f:
        f.writelines(missing_report)
    print(f"Wrote completeness report to {report_path}")

    # 4. Alignment Analysis
    reference_col, y_true = choose_reference_label(df)
    rows = []

    if len(rater_cols) >= 2:
        a = df[rater_cols[0]].map(label_to_binary).to_numpy(dtype=float)
        b = df[rater_cols[1]].map(label_to_binary).to_numpy(dtype=float)
        mask = np.isfinite(a) & np.isfinite(b)
        if mask.any():
            rows.append(
                {
                    "analysis": "inter_rater",
                    "reference_label": f"{rater_cols[0]} vs {rater_cols[1]}",
                    "metric": "cohens_kappa",
                    "n": int(mask.sum()),
                    "value": round(cohens_kappa(a, b), 6),
                    "ci95_lo": np.nan,
                    "ci95_hi": np.nan,
                }
            )

    if reference_col is None or y_true.size == 0 or np.isfinite(y_true).sum() == 0:
        print("No filled labels found for metrics calculation. Generating summary.md with status message.")
        summary_md = [
            "# Targeted Disagreement Analysis Summary\n",
            "## Status\n",
            "**Human evaluation metrics are PENDING independent annotation.**\n",
            "\nThis batch of 100 examples has been prepared for annotation. ",
            "See `batch_composition.csv` for details on the selection balance.\n"
        ]
        summary_md_path = input_path.with_name("analysis_summary.md")
        with open(summary_md_path, "w") as f:
            f.writelines(summary_md)
    else:
        for scorer_name, scorer_col in SCORERS.items():
            actual_col = None
            if scorer_col in df.columns:
                actual_col = scorer_col
            else:
                for alt in [f"{scorer_name.lower()}_score", f"local_{scorer_name.lower()}", f"{scorer_name.lower()}_hallucination_score"]:
                    if alt in df.columns:
                        actual_col = alt
                        break
            if not actual_col:
                continue
                
            score = pd.to_numeric(df[actual_col], errors="coerce").to_numpy(dtype=float)
            for metric_name, fn in [
                ("auroc", auroc),
                ("auprc", auprc),
                ("balanced_accuracy_at_0.5", balanced_accuracy),
            ]:
                val = fn(y_true, score)
                lo, hi = bootstrap_ci(
                    y_true,
                    score,
                    fn,
                    n_bootstrap=args.n_bootstrap,
                    seed=args.seed,
                )
                rows.append(
                    {
                        "analysis": "scorer_alignment",
                        "reference_label": reference_col,
                        "scorer": scorer_name,
                        "metric": metric_name,
                        "n": int((np.isfinite(y_true) & np.isfinite(score)).sum()),
                        "value": round(val, 6) if np.isfinite(val) else np.nan,
                        "ci95_lo": round(lo, 6) if np.isfinite(lo) else np.nan,
                        "ci95_hi": round(hi, 6) if np.isfinite(hi) else np.nan,
                    }
                )
            pearson, spearman = correlations(y_true, score)
            rows.extend(
                [
                    {
                        "analysis": "scorer_alignment",
                        "reference_label": reference_col,
                        "scorer": scorer_name,
                        "metric": "pearson",
                        "n": int((np.isfinite(y_true) & np.isfinite(score)).sum()),
                        "value": round(pearson, 6) if np.isfinite(pearson) else np.nan,
                        "ci95_lo": np.nan,
                        "ci95_hi": np.nan,
                    },
                    {
                        "analysis": "scorer_alignment",
                        "reference_label": reference_col,
                        "scorer": scorer_name,
                        "metric": "spearman",
                        "n": int((np.isfinite(y_true) & np.isfinite(score)).sum()),
                        "value": round(spearman, 6) if np.isfinite(spearman) else np.nan,
                        "ci95_lo": np.nan,
                        "ci95_hi": np.nan,
                    },
                ]
            )

    out = pd.DataFrame(rows)
    output = Path(args.output) if args.output else Path(args.input).with_name("analysis_summary.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False)
    if out.empty:
        print(f"Wrote empty analysis scaffold to {output}")
    else:
        print(out.to_string(index=False))
        print(f"Wrote {len(out)} rows to {output}")


if __name__ == "__main__":
    main()
