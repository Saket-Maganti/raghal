#!/usr/bin/env python3
"""Build the two ControlledRAG figures used in main paper:

  - metric_fragility_forest.pdf: forest plot of baseline-v1 contrasts
    on the same fixed generations under five scorer input formats.
    Values are from supplement Table 11
    (results/revision/context_conditioned_nli/contrasts_n600.csv).

  - slice_dependent_ranking.pdf: grouped bar chart of scorer-human
    Spearman correlations across the n=99 typical-row calibration and
    the n=100 targeted disagreement slice. Values are from
    human_eval_final/n99_calibration/{human_eval_correlations,
    bootstrap_correlation_cis}.csv and
    human_eval_final/n100_disagreement/{human_disagreement_correlations,
    human_disagreement_bootstrap_cis}.csv.

Both figures use grayscale-safe colors and small footprints suitable
for a NeurIPS 9-page main body.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent
plt.rcParams.update(
    {
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 9,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.linewidth": 0.6,
        "lines.linewidth": 0.8,
    }
)


def build_forest() -> None:
    rows = [
        ("Legacy DeBERTa-v3 proxy",       0.017, -0.003,  0.037),
        ("Legacy roberta-large-mnli",     0.044,  0.026,  0.063),
        ("Context-conditioned DeBERTa-v3", -0.279, -0.340, -0.219),
        ("Context-conditioned roberta-large-mnli", -0.081, -0.122, -0.043),
        ("Context-conditioned RAGAS-style judge",   0.130,  0.075,  0.186),
    ]

    fig, ax = plt.subplots(figsize=(5.0, 1.8))
    y = np.arange(len(rows))[::-1]
    means = np.array([r[1] for r in rows])
    los = np.array([r[2] for r in rows])
    his = np.array([r[3] for r in rows])
    err_low = means - los
    err_high = his - means

    ax.errorbar(
        means,
        y,
        xerr=[err_low, err_high],
        fmt="o",
        markersize=4.0,
        color="black",
        ecolor="black",
        elinewidth=0.8,
        capsize=2.5,
    )
    ax.axvline(0.0, color="0.45", linewidth=0.8, linestyle="--")

    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlabel("baseline $-$ aggressive-refinement (95% CI)")
    ax.set_xlim(-0.40, 0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", length=2)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="0.85", linewidth=0.4, linestyle=":")
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(OUT / "metric_fragility_forest.pdf", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def build_slice_bar() -> None:
    scorers = ["DeBERTa-v3", "roberta-large-mnli", "RAGAS-style"]
    n99_mean = np.array([0.103, 0.394, 0.549])
    n99_lo = np.array([-0.080, 0.222, 0.380])
    n99_hi = np.array([0.283, 0.543, 0.707])
    n100_mean = np.array([-0.156, 0.446, 0.384])
    n100_lo = np.array([-0.331, 0.293, 0.241])
    n100_hi = np.array([0.032, 0.581, 0.523])

    fig, ax = plt.subplots(figsize=(5.0, 2.2))
    x = np.arange(len(scorers))
    width = 0.36
    ax.bar(
        x - width / 2,
        n99_mean,
        width,
        yerr=[n99_mean - n99_lo, n99_hi - n99_mean],
        label=r"Typical-row calibration ($n=99$)",
        color="0.65",
        edgecolor="black",
        linewidth=0.6,
        capsize=2.5,
        error_kw={"linewidth": 0.8},
    )
    ax.bar(
        x + width / 2,
        n100_mean,
        width,
        yerr=[n100_mean - n100_lo, n100_hi - n100_mean],
        label=r"Targeted disagreement slice ($n=100$)",
        color="0.30",
        edgecolor="black",
        linewidth=0.6,
        capsize=2.5,
        error_kw={"linewidth": 0.8},
    )
    ax.axhline(0.0, color="0.4", linewidth=0.8, linestyle="-")
    # Annotate the y=0 line so the "no correlation" reference is explicit
    ax.text(
        len(scorers) - 0.55,
        0.02,
        "no correlation",
        color="0.35",
        fontsize=6.5,
        ha="right",
        va="bottom",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(scorers)
    ax.set_ylabel("Spearman $\\rho$ vs. adjudicated label")
    ax.set_ylim(-0.45, 0.85)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", length=2)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", color="0.85", linewidth=0.4, linestyle=":")
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, handlelength=1.2)

    fig.tight_layout()
    fig.savefig(OUT / "slice_dependent_ranking.pdf", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    build_forest()
    build_slice_bar()
    print("wrote", OUT / "metric_fragility_forest.pdf")
    print("wrote", OUT / "slice_dependent_ranking.pdf")
