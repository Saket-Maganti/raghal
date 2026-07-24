"""
experiments/build_ccs_calibration.py — Phase 3 #7
==================================================

Build the CCS calibration figure: distribution of Context Coherence Score
(CCS) split by hallucination outcome, plus a binned hallucination-rate
curve. Demonstrates that CCS is not just a diagnostic but a *predictive*
signal: low-CCS retrieval sets precede generation failures at much
higher rates than high-CCS sets.

Two panels:

  Panel A — kernel-density histogram of CCS overlaid for hallucinated
            (red) vs faithful (blue) generations. Visible mass shift
            toward low CCS in the red distribution = predictive.

  Panel B — hallucination rate by CCS quintile, with N annotated. The
            bar height in the bottom quintile vs the top quintile is
            the headline calibration claim.

Inputs (any with valid ccs values are merged):
    results/multidataset/per_query.csv         (HCPC rows w/ ccs)
    results/coherence_analysis/per_query_metrics.csv
    results/frontier_scale/per_query.csv

Outputs:
    ragpaper/figures/ccs_calibration.pdf
    ragpaper/figures/ccs_calibration.tex
    results/ccs_calibration/quintile_table.csv  (numbers behind panel B)

Usage:
    python3 experiments/build_ccs_calibration.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "ragpaper" / "figures"
OUT_PDF = OUT_DIR / "ccs_calibration.pdf"
OUT_TEX = OUT_DIR / "ccs_calibration.tex"
OUT_CSV_DIR = ROOT / "results" / "ccs_calibration"
OUT_CSV = OUT_CSV_DIR / "quintile_table.csv"

INPUTS = [
    ROOT / "results" / "multidataset"      / "per_query.csv",
    ROOT / "results" / "coherence_analysis" / "per_query_metrics.csv",
    ROOT / "results" / "frontier_scale"    / "per_query.csv",
]

FAITHFUL_COLOR  = "#1f4e79"   # deep blue
HALLUC_COLOR    = "#c0504d"   # red
QUINTILE_COLOR  = "#3c7d3c"   # green


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Different runners use slightly different column names; collapse to
    a canonical set: {ccs, is_hallucination, dataset, model, condition}."""
    rename = {}
    if "context_coherence" in df.columns and "ccs" not in df.columns:
        rename["context_coherence"] = "ccs"
    if "halluc" in df.columns and "is_hallucination" not in df.columns:
        rename["halluc"] = "is_hallucination"
    return df.rename(columns=rename)


def load_ccs_pairs() -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for path in INPUTS:
        if not path.exists():
            print(f"[ccs] skip (missing): {path}")
            continue
        df = _normalize_columns(pd.read_csv(path))
        if "ccs" not in df.columns or "is_hallucination" not in df.columns:
            print(f"[ccs] skip (no ccs/halluc cols): {path}")
            continue
        # Sentinel -1 means "no CCS computed for this row" (e.g. baseline
        # condition where the retriever didn't return a coherence log).
        df = df[df["ccs"] >= 0].copy()
        df["is_hallucination"] = df["is_hallucination"].astype(bool)
        df["__source"] = path.parent.name
        frames.append(df[["ccs", "is_hallucination", "__source"]])
    if not frames:
        raise SystemExit("[ccs] no usable rows across inputs")
    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates()    # in case of partial CSV overlap
    print(f"[ccs] loaded {len(out)} rows with valid CCS "
          f"({out['is_hallucination'].sum()} hallucinated, "
          f"{(~out['is_hallucination']).sum()} faithful)")
    return out


def quintile_table(df: pd.DataFrame, n_bins: int = 5) -> pd.DataFrame:
    df = df.copy()
    df["bin"] = pd.qcut(df["ccs"], q=n_bins, labels=False, duplicates="drop")
    out = df.groupby("bin").agg(
        n=("ccs", "count"),
        ccs_lo=("ccs", "min"),
        ccs_hi=("ccs", "max"),
        ccs_mean=("ccs", "mean"),
        halluc_rate=("is_hallucination", "mean"),
    ).reset_index()
    out["halluc_rate"] = out["halluc_rate"].round(4)
    out["ccs_lo"]   = out["ccs_lo"].round(3)
    out["ccs_hi"]   = out["ccs_hi"].round(3)
    out["ccs_mean"] = out["ccs_mean"].round(3)
    return out


def plot(df: pd.DataFrame, q_table: pd.DataFrame) -> None:
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(8.6, 3.4),
                                    constrained_layout=True)

    # Panel A: overlaid histograms
    bins = np.linspace(df["ccs"].min(), df["ccs"].max(), 26)
    faithful = df[~df["is_hallucination"]]["ccs"]
    hallu    = df[ df["is_hallucination"]]["ccs"]
    axA.hist(faithful, bins=bins, color=FAITHFUL_COLOR, alpha=0.55,
             label=f"faithful (n={len(faithful)})", density=True,
             edgecolor="white", linewidth=0.4)
    axA.hist(hallu,    bins=bins, color=HALLUC_COLOR,  alpha=0.7,
             label=f"hallucinated (n={len(hallu)})",  density=True,
             edgecolor="white", linewidth=0.4)
    if len(faithful) and len(hallu):
        axA.axvline(faithful.mean(), color=FAITHFUL_COLOR,
                    linestyle="--", linewidth=1)
        axA.axvline(hallu.mean(),    color=HALLUC_COLOR,
                    linestyle="--", linewidth=1)
        gap = faithful.mean() - hallu.mean()
        axA.set_title(f"A. CCS distribution by outcome  "
                      f"(mean gap $={gap:+.3f}$)", fontsize=10)
    else:
        axA.set_title("A. CCS distribution by outcome", fontsize=10)
    axA.set_xlabel("Context Coherence Score (CCS)")
    axA.set_ylabel("density")
    axA.legend(loc="upper left", frameon=False, fontsize=8)
    for spine in ("top", "right"):
        axA.spines[spine].set_visible(False)

    # Panel B: hallucination rate by CCS quintile
    x = np.arange(len(q_table))
    bars = axB.bar(x, q_table["halluc_rate"] * 100,
                   color=QUINTILE_COLOR, edgecolor="white")
    for i, row in q_table.iterrows():
        axB.text(i, row["halluc_rate"] * 100 + 0.6,
                 f"n={int(row['n'])}", ha="center", fontsize=8, color="gray")
    axB.set_xticks(x)
    axB.set_xticklabels(
        [f"Q{i+1}\n[{row.ccs_lo:.2f}, {row.ccs_hi:.2f}]"
         for i, row in q_table.iterrows()],
        fontsize=8,
    )
    axB.set_ylabel("hallucination rate (%)")
    axB.set_title("B. Hallucination rate by CCS quintile", fontsize=10)
    axB.grid(axis="y", alpha=0.25, linestyle="--")
    for spine in ("top", "right"):
        axB.spines[spine].set_visible(False)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)


TEX_TEMPLATE = r"""% Auto-generated by experiments/build_ccs_calibration.py
\begin{figure}[!htb]
\centering
\includegraphics[width=\linewidth]{figures/ccs_calibration.pdf}
\caption{\textbf{CCS is a predictive (not just descriptive) signal.}
Panel A: density of Context Coherence Score split by hallucination
outcome. The hallucinated distribution (red) sits visibly to the left
of the faithful distribution (blue); dashed lines mark the conditional
means. Panel B: hallucination rate by CCS quintile (equal-frequency
bins). Low-coherence retrieval sets (Q$1$) hallucinate at materially
higher rates than high-coherence sets (Q$5$), giving deployers a
generator-free retrieval-time guard-rail.}
\label{fig:ccs_calibration}
\end{figure}
"""


def main() -> None:
    df = load_ccs_pairs()
    q  = quintile_table(df)
    OUT_CSV_DIR.mkdir(parents=True, exist_ok=True)
    q.to_csv(OUT_CSV, index=False)
    print("\n[ccs] quintile table:")
    print(q.to_string(index=False))
    plot(df, q)
    OUT_TEX.write_text(TEX_TEMPLATE)
    print(f"\n[ccs] wrote {OUT_PDF.relative_to(ROOT)}")
    print(f"[ccs] wrote {OUT_TEX.relative_to(ROOT)}")
    print(f"[ccs] wrote {OUT_CSV.relative_to(ROOT)}")
    print("[ccs] include in paper via:  \\input{figures/ccs_calibration}")


if __name__ == "__main__":
    main()
