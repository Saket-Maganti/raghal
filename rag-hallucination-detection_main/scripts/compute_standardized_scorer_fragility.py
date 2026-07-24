#!/usr/bin/env python3
"""Compute standardized scorer-fragility contrasts from fixed generations.

The raw DeBERTa / second-NLI / RAGAS-style scores live on different
scales. This script keeps the original raw contrasts, then adds z-scored
and rank-normalized contrasts computed on the same fixed-generation rows.
It does not rescore any generations.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


METRICS = {
    "DeBERTa": "faith_deberta",
    "second_NLI": "faith_second_nli",
    "RAGAS_style": "faith_ragas",
}

CONTRASTS = {
    "baseline_minus_hcpc_v1": ("baseline", "hcpc_v1"),
    "hcpc_v2_minus_hcpc_v1": ("hcpc_v2", "hcpc_v1"),
}


def bootstrap_ci(values: np.ndarray, n_bootstrap: int, seed: int) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, values.size, size=(n_bootstrap, values.size))
    means = values[idx].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(lo), float(hi)


def zscore(series: pd.Series) -> pd.Series:
    mu = series.mean()
    sigma = series.std(ddof=0)
    if not np.isfinite(sigma) or sigma == 0:
        return pd.Series(np.nan, index=series.index)
    return (series - mu) / sigma


def add_score_spaces(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for _, col in METRICS.items():
        out[f"{col}_z"] = zscore(out[col])
        # Percentile ranks are on [0, 1]. Use average ranks for ties.
        out[f"{col}_rank"] = out[col].rank(method="average", pct=True)
    return out


def paired_key_columns(df: pd.DataFrame) -> list[str]:
    candidates = ["dataset", "seed", "question"]
    return [c for c in candidates if c in df.columns]


def paired_differences(
    df: pd.DataFrame,
    value_col: str,
    left_condition: str,
    right_condition: str,
) -> np.ndarray:
    keys = paired_key_columns(df)
    if not keys:
        raise ValueError("No key columns available for paired contrasts")
    sub = df[df["condition"].isin([left_condition, right_condition])].copy()
    wide = sub.pivot_table(
        index=keys,
        columns="condition",
        values=value_col,
        aggfunc="mean",
    )
    needed = [left_condition, right_condition]
    wide = wide.dropna(subset=needed)
    return (wide[left_condition] - wide[right_condition]).to_numpy(dtype=float)


def summarize(df: pd.DataFrame, n_bootstrap: int, seed: int) -> pd.DataFrame:
    rows = []
    spaces: Iterable[tuple[str, str]] = (
        ("raw", "{col}"),
        ("z", "{col}_z"),
        ("rank", "{col}_rank"),
    )
    for metric_name, metric_col in METRICS.items():
        for score_space, template in spaces:
            value_col = template.format(col=metric_col)
            for contrast_name, (left, right) in CONTRASTS.items():
                diffs = paired_differences(df, value_col, left, right)
                lo, hi = bootstrap_ci(diffs, n_bootstrap=n_bootstrap, seed=seed)
                rows.append(
                    {
                        "metric": metric_name,
                        "score_space": score_space,
                        "contrast": contrast_name,
                        "left_condition": left,
                        "right_condition": right,
                        "n_pairs": int(np.isfinite(diffs).sum()),
                        "mean_diff": round(float(np.nanmean(diffs)), 6),
                        "ci95_lo": round(lo, 6),
                        "ci95_hi": round(hi, 6),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/revision/fix_03/per_query.csv",
        help="Fixed-generation metric-fragility rows.",
    )
    parser.add_argument(
        "--output",
        default="results/revision/fix_03/standardized_scorer_fragility.csv",
    )
    parser.add_argument("--n_bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    required = {"condition", *METRICS.values()}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    df = df[df["condition"].isin({"baseline", "hcpc_v1", "hcpc_v2"})].copy()
    df = df.dropna(subset=list(METRICS.values()))
    df = add_score_spaces(df)
    out = summarize(df, n_bootstrap=args.n_bootstrap, seed=args.seed)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False)
    print(f"Wrote {len(out)} rows to {output}")


if __name__ == "__main__":
    main()
