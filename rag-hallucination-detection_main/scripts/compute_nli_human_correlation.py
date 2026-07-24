#!/usr/bin/env python3
"""Summarize NLI-vs-human alignment for the n=99 calibration slice."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results/revision/context_conditioned_nli/n99_alignment_spearmans.csv"
OUTPUT = ROOT / "results/revision/context_conditioned_nli/n99_alignment_summary.csv"


def main() -> None:
    df = pd.read_csv(INPUT)
    cols = ["scorer", "column", "spearman_rho", "ci_lo", "ci_hi", "n"]
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise ValueError(f"{INPUT} is missing required columns: {missing}")

    out = df[cols].copy()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT, index=False)

    print("NLI-vs-human alignment on n=99 calibration slice:")
    print(out.to_string(index=False))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
