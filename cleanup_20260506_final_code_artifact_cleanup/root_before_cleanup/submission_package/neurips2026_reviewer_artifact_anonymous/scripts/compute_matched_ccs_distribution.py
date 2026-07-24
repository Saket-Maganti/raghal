#!/usr/bin/env python3
"""Summarize matched HIGH/LOW CCS score distributions."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/revision/fix_01/per_query.csv")
    parser.add_argument("--output_dir", default="results/revision/fix_01")
    parser.add_argument("--thresholds", nargs="+", type=float, default=[0.3, 0.4, 0.5, 0.6, 0.7])
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df = df[df["set_type"].isin(["high_ccs", "low_ccs"])].copy()
    rows = []
    for group, sub in df.groupby("set_type", sort=True):
        faith = pd.to_numeric(sub["faithfulness_score"], errors="coerce")
        rows.append(
            {
                "set_type": group,
                "n": int(faith.notna().sum()),
                "mean": round(float(faith.mean()), 6),
                "p10": round(float(faith.quantile(0.10)), 6),
                "p25": round(float(faith.quantile(0.25)), 6),
                "p50": round(float(faith.quantile(0.50)), 6),
                "p75": round(float(faith.quantile(0.75)), 6),
                "p90": round(float(faith.quantile(0.90)), 6),
            }
        )
    q = pd.DataFrame(rows)

    rate_rows = []
    for thr in args.thresholds:
        rec = {"threshold": thr}
        for group, sub in df.groupby("set_type", sort=True):
            faith = pd.to_numeric(sub["faithfulness_score"], errors="coerce")
            rec[f"{group}_hallucination_rate"] = round(float((faith < thr).mean()), 6)
        rate_rows.append(rec)
    rates = pd.DataFrame(rate_rows)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    q.to_csv(out_dir / "matched_ccs_faithfulness_quantiles.csv", index=False)
    rates.to_csv(out_dir / "matched_ccs_threshold_rates.csv", index=False)
    print(f"Wrote matched CCS summaries to {out_dir}")


if __name__ == "__main__":
    main()
