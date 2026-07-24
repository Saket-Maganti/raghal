#!/usr/bin/env python3
"""Add bootstrap/Wilson intervals to the cost-aware head-to-head table."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def bootstrap_mean_ci(values: np.ndarray, n_bootstrap: int, seed: int) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, values.size, size=(n_bootstrap, values.size))
    means = values[idx].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(lo), float(hi)


def wilson_ci(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return np.nan, np.nan
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    radius = z * np.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return float(center - radius), float(center + radius)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/revision/fix_06/per_query_compact.csv")
    parser.add_argument("--output", default="results/revision/fix_06/h2h_summary_with_ci.csv")
    parser.add_argument("--n_bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    if "error" in df.columns:
        df = df[df["error"].fillna("").astype(str).eq("")].copy()
    rows = []
    for (dataset, condition), sub in df.groupby(["dataset", "condition"], sort=True):
        faith = pd.to_numeric(sub["faithfulness_score"], errors="coerce").to_numpy(dtype=float)
        halluc = sub["is_hallucination"].astype(bool).to_numpy()
        latency = pd.to_numeric(sub["total_latency_ms"], errors="coerce").to_numpy(dtype=float)
        faith_lo, faith_hi = bootstrap_mean_ci(faith, args.n_bootstrap, args.seed)
        lat_lo, lat_hi = bootstrap_mean_ci(latency, args.n_bootstrap, args.seed)
        hall_lo, hall_hi = wilson_ci(int(halluc.sum()), len(halluc))
        rows.append(
            {
                "dataset": dataset,
                "condition": condition,
                "n": int(len(sub)),
                "faithfulness": round(float(np.nanmean(faith)), 6),
                "faith_ci95_lo": round(faith_lo, 6),
                "faith_ci95_hi": round(faith_hi, 6),
                "hallucination_rate": round(float(halluc.mean()), 6),
                "hallucination_ci95_lo": round(hall_lo, 6),
                "hallucination_ci95_hi": round(hall_hi, 6),
                "mean_latency_ms": round(float(np.nanmean(latency)), 6),
                "latency_ci95_lo_ms": round(lat_lo, 6),
                "latency_ci95_hi_ms": round(lat_hi, 6),
                "base_index_s": round(float(pd.to_numeric(sub["base_index_s"], errors="coerce").max()), 6),
                "raptor_index_s": round(float(pd.to_numeric(sub["raptor_index_s"], errors="coerce").max()), 6),
            }
        )
    out = pd.DataFrame(rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False)
    print(f"Wrote {len(out)} rows to {output}")


if __name__ == "__main__":
    main()
