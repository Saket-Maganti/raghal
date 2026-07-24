"""
Fix 9: self-confidence cross-validation strengthening.

Computes partial correlations between CCS and model self-confidence after
controlling for mean query-passage similarity and redundancy.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from experiments.revision_utils import ensure_dirs, write_markdown_table


OUT_DATA = Path("data/revision/fix_09")
OUT_RESULTS = Path("results/revision/fix_09")


def residualize(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    X = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ beta


def partial_corr(df: pd.DataFrame, controls: list[str]) -> pd.DataFrame:
    needed = ["ccs", "self_confidence"] + controls
    sub = df[needed].dropna()
    rows = []
    if len(sub) < 10:
        return pd.DataFrame()
    x = sub["ccs"].to_numpy(float)
    y = sub["self_confidence"].to_numpy(float)
    X = sub[controls].to_numpy(float) if controls else np.empty((len(sub), 0))
    if controls:
        xr = residualize(x, X)
        yr = residualize(y, X)
    else:
        xr, yr = x, y
    r, p = pearsonr(xr, yr)
    rho, sp = spearmanr(xr, yr)
    rows.append({
        "n": int(len(sub)),
        "controls": ",".join(controls) if controls else "none",
        "partial_pearson_r": round(float(r), 6),
        "partial_pearson_p": float(p),
        "partial_spearman_rho": round(float(rho), 6),
        "partial_spearman_p": float(sp),
        "survives": bool(p < 0.05 and r > 0),
    })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/confidence_calibration/per_query.csv")
    parser.add_argument("--ccs_col", default="ccs")
    parser.add_argument("--confidence_col", default="self_confidence")
    parser.add_argument("--mean_sim_col", default="mean_retrieval_similarity")
    parser.add_argument("--redundancy_col", default="passage_redundancy")
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS)
    df = pd.read_csv(args.input).rename(columns={
        args.ccs_col: "ccs",
        args.confidence_col: "self_confidence",
        args.mean_sim_col: "mean_retrieval_similarity",
        args.redundancy_col: "passage_redundancy",
    })
    # If redundancy is absent, use CCS as a weak placeholder only to force a
    # clear "not available" result; do not treat this as the final run.
    if "passage_redundancy" not in df.columns:
        df["passage_redundancy"] = np.nan

    rows = [
        partial_corr(df, []),
        partial_corr(df, ["mean_retrieval_similarity"]) if "mean_retrieval_similarity" in df.columns else pd.DataFrame(),
        partial_corr(df, ["mean_retrieval_similarity", "passage_redundancy"]) if "mean_retrieval_similarity" in df.columns else pd.DataFrame(),
    ]
    out = pd.concat([r for r in rows if not r.empty], ignore_index=True) if rows else pd.DataFrame()
    df.to_csv(OUT_DATA / "input_copy.csv", index=False)
    out.to_csv(OUT_RESULTS / "partial_correlations.csv", index=False)
    write_markdown_table(OUT_RESULTS / "summary.md", "Fix 9 - partial correlations", {"Partial Correlations": out})


if __name__ == "__main__":
    main()
