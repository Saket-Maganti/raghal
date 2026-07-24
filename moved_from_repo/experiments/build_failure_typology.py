"""
experiments/build_failure_typology.py — Phase 7 #7
====================================================

Find queries where HCPC-v$2$ STILL hallucinates and categorise the
failure modes. Reviewer concern: "you say HCPC-v$2$ recovers, but you
don't analyse where it doesn't."

A query is an HCPC-v$2$ FAILURE if:
    is_hallucination == True for HCPC-v$2$, AND
    is_hallucination == False for baseline (i.e., we made it WORSE)

OR if:
    is_hallucination == True for HCPC-v$2$, AND for baseline (i.e.,
    we failed to fix a problem the baseline already had)

We extract up to 20 failures, and for each compute:
    - dataset, model, question, ground_truth, all 3 answers
    - CCS (the gate decision input)
    - retrieval similarity
    - whether HCPC-v$2$ refined or not (gate_fired)
    - heuristic failure category:
        "type-A: gate fired, refinement made it worse"
        "type-B: gate didn't fire, baseline-incoherent set"
        "type-C: both gates wrong, set is genuinely hard"

Outputs:
    results/failure_typology/per_failure.csv
    results/failure_typology/typology_counts.csv
    results/failure_typology/summary.md

Usage:
    python3 experiments/build_failure_typology.py --top 20
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "results" / "failure_typology"

INPUTS = [
    ROOT / "results" / "scaled_headline" / "per_query.csv",
    ROOT / "results" / "multidataset"     / "per_query.csv",
    ROOT / "results" / "headtohead"        / "per_query.csv",
]


def _load() -> pd.DataFrame:
    frames = []
    for p in INPUTS:
        if not p.exists():
            continue
        df = pd.read_csv(p)
        if "is_hallucination" not in df.columns or "condition" not in df.columns:
            continue
        df["is_hallucination"] = df["is_hallucination"].astype(bool)
        frames.append(df)
    if not frames:
        raise SystemExit("[failure-typology] no usable inputs")
    return pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["dataset", "model", "question", "condition"], keep="last")


def _classify(row, gate_fired):
    """Heuristic typology of HCPC-v$2$ failures."""
    base_h = bool(row.get("baseline_halluc", False))
    v2_h = bool(row.get("v2_halluc", True))
    if not v2_h:
        return None
    if gate_fired and not base_h:
        return "type-A: gate fired, refinement made it worse"
    if not gate_fired and base_h:
        return "type-B: gate did not fire on baseline-incoherent set"
    return "type-C: both gates wrong; set is genuinely hard"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20,
                    help="how many failures to dump in detail")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = _load()

    # Pivot: one row per (dataset, model, question), columns per condition
    pivoted = df.pivot_table(
        index=["dataset", "model", "question"],
        columns="condition",
        values=["faithfulness_score", "is_hallucination", "answer", "ccs",
                "mean_retrieval_similarity", "refined"],
        aggfunc="first",
    )
    pivoted.columns = [f"{c[0]}__{c[1]}" for c in pivoted.columns]
    pivoted = pivoted.reset_index()

    # We need at least baseline and hcpc_v2 columns
    need_cols = ["is_hallucination__baseline", "is_hallucination__hcpc_v2"]
    if not all(c in pivoted.columns for c in need_cols):
        raise SystemExit(f"[failure-typology] missing required cols; have {list(pivoted.columns)[:10]}")

    pivoted["baseline_halluc"] = pivoted["is_hallucination__baseline"].fillna(False).astype(bool)
    pivoted["v2_halluc"] = pivoted["is_hallucination__hcpc_v2"].fillna(False).astype(bool)
    pivoted["v2_refined"] = pivoted.get("refined__hcpc_v2",
                                          pd.Series([False] * len(pivoted))).fillna(False).astype(bool)

    failures = pivoted[pivoted["v2_halluc"]].copy()
    failures["category"] = failures.apply(
        lambda r: _classify(r, r["v2_refined"]), axis=1)
    failures = failures.dropna(subset=["category"])
    print(f"[failure-typology] {len(failures)} HCPC-v2 failures of "
          f"{len(pivoted)} total queries "
          f"({100*len(failures)/max(1,len(pivoted)):.1f}%)")

    # Categorise
    counts = Counter(failures["category"].tolist())
    for cat, n in counts.most_common():
        print(f"  {n:>4}  {cat}")

    # Sort failures by largest faith drop (baseline → v2)
    if "faithfulness_score__baseline" in failures.columns and \
       "faithfulness_score__hcpc_v2" in failures.columns:
        failures["faith_drop"] = (
            failures["faithfulness_score__baseline"].fillna(0)
            - failures["faithfulness_score__hcpc_v2"].fillna(0))
        failures = failures.sort_values("faith_drop", ascending=False)

    # Dump top N
    top = failures.head(args.top)
    top.to_csv(OUT_DIR / "per_failure.csv", index=False)
    print(f"[failure-typology] wrote {OUT_DIR / 'per_failure.csv'}")

    # Counts
    counts_df = pd.DataFrame(
        [{"category": k, "n": v} for k, v in counts.most_common()])
    counts_df.to_csv(OUT_DIR / "typology_counts.csv", index=False)

    # Markdown summary
    md = ["# HCPC-v2 failure typology (Phase 7 #7)", "",
          f"Total HCPC-v2 failures: {len(failures)} of {len(pivoted)} ",
          f"queries ({100*len(failures)/max(1,len(pivoted)):.1f}%).", "",
          "## Counts by category", "",
          counts_df.to_markdown(index=False) if not counts_df.empty else "(no failures)",
          "",
          f"## Top {args.top} failures (sorted by baseline → v2 faith drop)",
          ""]
    if not top.empty:
        cols_to_show = ["dataset", "model", "question",
                         "category", "v2_refined",
                         "faithfulness_score__baseline",
                         "faithfulness_score__hcpc_v1",
                         "faithfulness_score__hcpc_v2",
                         "ccs__hcpc_v2"]
        cols_present = [c for c in cols_to_show if c in top.columns]
        md.append(top[cols_present].to_markdown(index=False))
    (OUT_DIR / "summary.md").write_text("\n".join(md))
    print(f"[failure-typology] wrote {OUT_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()
