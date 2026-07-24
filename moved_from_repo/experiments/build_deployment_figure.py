"""
experiments/build_deployment_figure.py — Phase 2 Item 9 (deployment case study)
================================================================================

Purpose
-------
Turn the already-collected per-query CSVs into a *deployment-relevant* picture:
    "If I deploy this system at 1000 QPD on my M4 mini, which retrieval
     condition dominates on the latency–faithfulness frontier?"

We do **not** re-run any queries — this script only reads existing results:

    results/headtohead/per_query.csv          (has latency_s per query)
    results/multidataset/per_query.csv        (faith + hallucination + ccs)
    results/multi_retriever/per_query.csv     (embedder comparison)

and emits:

    results/deployment_figure/latency_vs_faith.png
    results/deployment_figure/pareto_summary.csv
    results/deployment_figure/deployment_table.md

The figure is the one reviewers ask for:  x = median latency (s),  y = mean
faithfulness, marker = condition, colour = dataset.  A Pareto frontier line
is drawn so the "pick this retriever" story is visual, not textual.

Design choices
--------------
* No new dependencies beyond matplotlib + pandas (already in env).
* Uses **median** latency rather than mean to avoid the well-known cold-start
  outliers (e.g. std=91 on squad/1024 baseline).
* Refuses to plot a condition with < MIN_QUERIES samples so stray configs do
  not skew the story.
* Pareto frontier computed in (latency↓, faith↑) space — the standard
  dominance test: (l_a ≤ l_b) AND (f_a ≥ f_b) with at least one strict.

Usage
-----
    python experiments/build_deployment_figure.py
    python experiments/build_deployment_figure.py --min_queries 20
    python experiments/build_deployment_figure.py --datasets squad pubmedqa
"""

from __future__ import annotations

import argparse
import os
from typing import List, Optional

import pandas as pd

# matplotlib is imported lazily in main() so `--help` works on headless hosts
# that lack a display.

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

OUT_DIR = os.path.join(ROOT, "results", "deployment_figure")

SOURCES = {
    "headtohead": os.path.join(ROOT, "results", "headtohead",   "per_query.csv"),
    "multidata":  os.path.join(ROOT, "results", "multidataset", "per_query.csv"),
    "multiret":   os.path.join(ROOT, "results", "multi_retriever", "per_query.csv"),
}


# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────

def _read_if_exists(path: str, source_tag: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        print(f"[deploy] missing {source_tag}: {path}")
        return None
    df = pd.read_csv(path)
    df["source"] = source_tag
    return df


def load_all() -> pd.DataFrame:
    """Union the three per_query CSVs on their common schema.

    Common columns: condition, faithfulness_score, is_hallucination, dataset.
    `latency_s` exists only in headtohead; we treat the other sources as
    "indexed retrieval cost" = 0 for those rows, because they were run under
    a different latency regime and shouldn't be mixed into timing.  In
    practice we only *plot* rows that have real latency numbers.
    """
    frames: List[pd.DataFrame] = []
    for tag, path in SOURCES.items():
        df = _read_if_exists(path, tag)
        if df is None:
            continue
        keep = ["condition", "faithfulness_score", "is_hallucination", "dataset",
                "mean_retrieval_similarity", "source"]
        if "latency_s" in df.columns:
            keep.append("latency_s")
        else:
            df["latency_s"] = float("nan")
            keep.append("latency_s")
        if "model" in df.columns:
            keep.append("model")
        else:
            df["model"] = "unknown"
            keep.append("model")
        frames.append(df[keep].copy())
    if not frames:
        raise RuntimeError("no per_query.csv files found — run the short-form "
                           "experiments first.")
    out = pd.concat(frames, ignore_index=True)
    out["is_hallucination"] = out["is_hallucination"].astype(bool)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Aggregation + Pareto
# ─────────────────────────────────────────────────────────────────────────────

def aggregate(df: pd.DataFrame, min_queries: int) -> pd.DataFrame:
    """One row per (dataset, condition) with median latency + mean faith.

    Drops rows with no latency (mostly the multidataset sweep which ran
    without wall-clock instrumentation).  Requires ≥ min_queries per group.
    """
    timed = df.dropna(subset=["latency_s"]).copy()
    g = timed.groupby(["dataset", "condition"], as_index=False).agg(
        n=("faithfulness_score", "count"),
        faith=("faithfulness_score", "mean"),
        halluc_rate=("is_hallucination", "mean"),
        sim=("mean_retrieval_similarity", "mean"),
        median_latency=("latency_s", "median"),
        p95_latency=("latency_s", lambda s: s.quantile(0.95)),
    )
    g = g[g["n"] >= min_queries].copy()
    for col in ("faith", "halluc_rate", "sim", "median_latency", "p95_latency"):
        g[col] = g[col].round(4)
    return g.sort_values(["dataset", "median_latency"]).reset_index(drop=True)


def pareto_frontier(agg: pd.DataFrame) -> pd.DataFrame:
    """Mark rows on the (latency↓, faith↑) Pareto frontier *within each dataset*.

    A row is Pareto-optimal iff no other row in the same dataset has
    (latency ≤ it) AND (faith ≥ it) with at least one strict inequality.
    """
    agg = agg.copy()
    agg["pareto"] = False
    for ds, sub in agg.groupby("dataset"):
        rows = sub.to_dict("records")
        for i, a in enumerate(rows):
            dominated = False
            for j, b in enumerate(rows):
                if i == j:
                    continue
                if (b["median_latency"] <= a["median_latency"]
                        and b["faith"] >= a["faith"]
                        and (b["median_latency"] < a["median_latency"]
                             or b["faith"] > a["faith"])):
                    dominated = True
                    break
            if not dominated:
                agg.loc[(agg["dataset"] == ds) &
                        (agg["condition"] == a["condition"]), "pareto"] = True
    return agg


# ─────────────────────────────────────────────────────────────────────────────
# Plotting
# ─────────────────────────────────────────────────────────────────────────────

def make_figure(agg: pd.DataFrame, out_png: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    datasets = sorted(agg["dataset"].unique())
    conditions = sorted(agg["condition"].unique())

    # Colour per dataset, marker per condition — so a reviewer can read either.
    cmap = plt.get_cmap("tab10")
    ds_colors = {d: cmap(i % 10) for i, d in enumerate(datasets)}
    marker_cycle = ["o", "s", "^", "D", "v", "P", "X", "*", "<", ">"]
    cond_markers = {c: marker_cycle[i % len(marker_cycle)]
                    for i, c in enumerate(conditions)}

    fig, ax = plt.subplots(figsize=(8, 5.5))

    for _, r in agg.iterrows():
        ax.scatter(
            r["median_latency"], r["faith"],
            s=120 if r["pareto"] else 60,
            color=ds_colors[r["dataset"]],
            marker=cond_markers[r["condition"]],
            edgecolors="black" if r["pareto"] else "none",
            linewidths=1.4 if r["pareto"] else 0,
            alpha=0.95,
        )
        ax.annotate(
            f"{r['condition']}",
            (r["median_latency"], r["faith"]),
            xytext=(4, 4), textcoords="offset points",
            fontsize=7.5, alpha=0.8,
        )

    # Dataset-coloured Pareto polylines.
    for ds, sub in agg[agg["pareto"]].groupby("dataset"):
        pts = sub.sort_values("median_latency")
        ax.plot(pts["median_latency"], pts["faith"],
                color=ds_colors[ds], linestyle="--", linewidth=1.2, alpha=0.55)

    ax.set_xlabel("Median latency per query (s) — lower is better")
    ax.set_ylabel("Mean NLI faithfulness — higher is better")
    ax.set_title("Deployment view: latency vs faithfulness\n"
                 "(dashed = per-dataset Pareto frontier; black-edge = on frontier)")
    ax.grid(True, alpha=0.25)

    # Two legends: colour = dataset, marker = condition.
    from matplotlib.lines import Line2D
    ds_handles = [Line2D([0], [0], marker="o", color="w",
                         markerfacecolor=ds_colors[d], markersize=8, label=d)
                  for d in datasets]
    cond_handles = [Line2D([0], [0], marker=cond_markers[c], color="black",
                           linestyle="none", markersize=7, label=c)
                    for c in conditions]
    leg1 = ax.legend(handles=ds_handles,   title="dataset",
                     loc="lower right", fontsize=8)
    ax.add_artist(leg1)
    ax.legend(handles=cond_handles, title="condition",
              loc="upper right", fontsize=8)

    fig.tight_layout()
    fig.savefig(out_png, dpi=180)
    plt.close(fig)
    print(f"[deploy] wrote {out_png}")


# ─────────────────────────────────────────────────────────────────────────────
# Markdown report
# ─────────────────────────────────────────────────────────────────────────────

def write_markdown(agg: pd.DataFrame, out_md: str) -> None:
    lines: List[str] = [
        "# Deployment case study — latency vs faithfulness",
        "",
        "Source: existing `per_query.csv` from head-to-head, multidataset, and "
        "multi-retriever sweeps. No new runs.",
        "",
        "## Per-dataset Pareto frontier (latency↓, faith↑)",
        "",
    ]
    for ds, sub in agg.groupby("dataset"):
        lines.append(f"### {ds}")
        lines.append("")
        lines.append("| condition | n | median_lat (s) | p95_lat (s) | faith | halluc | on_pareto |")
        lines.append("|---|---:|---:|---:|---:|---:|:---:|")
        for _, r in sub.sort_values("median_latency").iterrows():
            lines.append(
                f"| {r['condition']} | {int(r['n'])} | "
                f"{r['median_latency']:.2f} | {r['p95_latency']:.2f} | "
                f"{r['faith']:.3f} | {r['halluc_rate']:.3f} | "
                f"{'✅' if r['pareto'] else ''} |"
            )
        lines.append("")

    frontier = agg[agg["pareto"]].sort_values(["dataset", "faith"], ascending=[True, False])
    lines += [
        "## Deployment takeaway",
        "",
        "Picks on the frontier (choose per dataset):",
        "",
    ]
    for _, r in frontier.iterrows():
        lines.append(
            f"- **{r['dataset']}**: `{r['condition']}` — "
            f"{r['median_latency']:.2f}s / faith={r['faith']:.3f} / "
            f"halluc={r['halluc_rate']:.3f}"
        )
    lines.append("")
    with open(out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"[deploy] wrote {out_md}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min_queries", type=int, default=15,
                    help="drop (dataset,condition) groups with fewer than N queries")
    ap.add_argument("--datasets", nargs="+", default=None,
                    help="subset of datasets to plot (default = all present)")
    ap.add_argument("--out_dir", default=OUT_DIR)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    raw = load_all()
    if args.datasets:
        raw = raw[raw["dataset"].isin(args.datasets)].copy()
        if raw.empty:
            raise SystemExit(f"no rows after filtering to {args.datasets}")

    agg = aggregate(raw, min_queries=args.min_queries)
    if agg.empty:
        raise SystemExit(
            "no (dataset,condition) groups survived --min_queries; "
            "either lower the threshold or run the head-to-head sweep first."
        )
    agg = pareto_frontier(agg)

    summary_csv = os.path.join(args.out_dir, "pareto_summary.csv")
    agg.to_csv(summary_csv, index=False)
    print(f"[deploy] wrote {summary_csv}  ({len(agg)} rows)")

    make_figure(agg, os.path.join(args.out_dir, "latency_vs_faith.png"))
    write_markdown(agg, os.path.join(args.out_dir, "deployment_table.md"))


if __name__ == "__main__":
    main()
