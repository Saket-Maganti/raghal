"""
experiments/build_headline_figure.py — Phase 3 #1
==================================================

Build the frontier-scale headline figure: paradox magnitude vs generator
scale across 7B → 70B → 120B, with HCPC-v2 recovery overlaid. This is
the single plot that should answer "does the paradox persist at scale?"
without a reviewer needing to read the table.

Inputs:
    results/multidataset/summary.csv          (Mistral-7B, Llama3-8B reference)
    results/frontier_scale/paradox_by_scale.csv (Llama-70B, GPT-OSS-120B)

Output:
    ragpaper/figures/headline_frontier.pdf    (LaTeX-includable, vector)
    ragpaper/figures/headline_frontier.tex    (figure environment + caption)

Usage:
    python3 experiments/build_headline_figure.py

The TeX wrapper is auto-generated so you can `\input{figures/headline_frontier}`
from results.tex — no manual figure-environment plumbing required.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # no display needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "ragpaper" / "figures"
OUT_PDF = OUT_DIR / "headline_frontier.pdf"
OUT_TEX = OUT_DIR / "headline_frontier.tex"

PRIMARY  = "#1f4e79"        # deep blue — baseline
SECONDARY = "#c0504d"       # red — hcpc_v1 (paradox dip)
TERTIARY  = "#3c7d3c"       # green — hcpc_v2 (recovery)


def _load_7b_reference() -> pd.DataFrame:
    """Pull Mistral-7B paradox rows for SQuAD and PubMedQA from the
    multidataset summary so the figure shows 7B → 70B → 120B as one curve."""
    df = pd.read_csv(ROOT / "results" / "multidataset" / "summary.csv")
    df = df[df["model"] == "mistral"]
    df = df[df["dataset"].isin(["squad", "pubmedqa"])]
    rows = []
    for ds, sub in df.groupby("dataset"):
        try:
            base = float(sub[sub["condition"] == "baseline"]["faith"].iloc[0])
            v1   = float(sub[sub["condition"] == "hcpc_v1"]["faith"].iloc[0])
            v2   = float(sub[sub["condition"] == "hcpc_v2"]["faith"].iloc[0])
        except (IndexError, KeyError):
            continue
        rows.append({
            "dataset": ds,
            "model":   "Mistral-7B",
            "scale":   "7B",
            "scale_n": 7,
            "faith_base": base,
            "faith_v1":   v1,
            "faith_v2":   v2,
            "paradox":    base - v1,
            "recovery":   v2 - v1,
        })
    return pd.DataFrame(rows)


def _load_frontier() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "results" / "frontier_scale" / "paradox_by_scale.csv")
    label_map = {"llama-3.3-70b": "Llama-3.3-70B",
                 "gpt-oss-120b":  "GPT-OSS-120B"}
    scale_n = {"70B": 70, "120B": 120}
    df["model"]    = df["model"].map(lambda m: label_map.get(m, m))
    df["scale_n"]  = df["scale"].map(scale_n)
    return df.rename(columns={
        "paradox_drop": "paradox",
        "v2_recovery":  "recovery",
    })[["dataset", "model", "scale", "scale_n",
        "faith_base", "faith_v1", "faith_v2", "paradox", "recovery"]]


def build_dataframe() -> pd.DataFrame:
    df = pd.concat([_load_7b_reference(), _load_frontier()], ignore_index=True)
    df = df.sort_values(["dataset", "scale_n"]).reset_index(drop=True)
    return df


def plot(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(
        1, 2, figsize=(8.6, 3.5), sharey=False, constrained_layout=True,
    )
    datasets = ["squad", "pubmedqa"]
    titles = {"squad": "SQuAD (short-span QA)",
              "pubmedqa": "PubMedQA (biomedical)"}

    bar_w = 0.25
    for ax, ds in zip(axes, datasets):
        sub = df[df["dataset"] == ds].reset_index(drop=True)
        x = np.arange(len(sub))
        ax.bar(x - bar_w, sub["faith_base"], bar_w,
               color=PRIMARY,   label="baseline")
        ax.bar(x,         sub["faith_v1"],   bar_w,
               color=SECONDARY, label="HCPC-v1 (refine all)")
        ax.bar(x + bar_w, sub["faith_v2"],   bar_w,
               color=TERTIARY,  label="HCPC-v2 (selective)")

        # Paradox magnitude annotation between baseline and v1
        for i, row in sub.iterrows():
            par = row["paradox"]
            if abs(par) >= 0.005:
                y = max(row["faith_base"], row["faith_v1"]) + 0.02
                ax.annotate(
                    f"$\\Delta={par:+.3f}$",
                    xy=(i - bar_w/2, y),
                    ha="center", va="bottom", fontsize=8,
                    color=SECONDARY if par > 0 else "gray",
                )

        ax.set_xticks(x)
        ax.set_xticklabels([f"{m}\n({s})" for m, s in zip(sub["model"], sub["scale"])],
                           fontsize=8)
        ax.set_ylim(0.0, max(sub[["faith_base","faith_v1","faith_v2"]].max())*1.18)
        ax.set_ylabel("faithfulness (NLI)" if ds == "squad" else "")
        ax.set_title(titles[ds], fontsize=10)
        ax.grid(axis="y", alpha=0.25, linestyle="--")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

    # Single legend across both panels
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels,
               loc="upper center", bbox_to_anchor=(0.5, -0.03),
               ncol=3, frameon=False, fontsize=9)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)


TEX_TEMPLATE = r"""% Auto-generated by experiments/build_headline_figure.py
\begin{figure}[!t]
\centering
\includegraphics[width=\linewidth]{figures/headline_frontier.pdf}
\caption{\textbf{The refinement paradox persists at frontier scale.}
Per-passage refinement (HCPC-v1, red) drops faithfulness below the
no-refinement baseline (blue) on SQuAD across a $17\times$ generator
scale range (Mistral-$7$B $\to$ Llama-$3.3$-$70$B $\to$ GPT-OSS-$120$B).
HCPC-v$2$ (green), which gates refinement on a coherence-loss check,
recovers the lost faithfulness on every cell.  Paradox magnitude
$\Delta=\textrm{faith}_{\textrm{base}}-\textrm{faith}_{\textrm{v1}}$
annotated above each pair.  PubMedQA paradox attenuates at scale --- a
prediction the coherence account makes (stronger parametric priors are
better substitutes for fragmented biomedical evidence) --- but does
not invert.  See \S\ref{sec:rob:frontier} for the full table.}
\label{fig:headline_frontier}
\end{figure}
"""


def main() -> None:
    df = build_dataframe()
    print("[headline] data:")
    print(df.round(3).to_string(index=False))
    plot(df)
    OUT_TEX.write_text(TEX_TEMPLATE)
    print(f"\n[headline] wrote {OUT_PDF.relative_to(ROOT)}")
    print(f"[headline] wrote {OUT_TEX.relative_to(ROOT)}")
    print("[headline] include in paper via:  \\input{figures/headline_frontier}")


if __name__ == "__main__":
    main()
