"""
experiments/build_human_eval_samples.py — Phase 7 #6
=====================================================

Sample N queries (default 100) for single-rater human validation of
the NLI faithfulness scores. Output is a JSONL where each row carries
the question, generated answer, retrieved context (truncated for
readability), the NLI faithfulness score we computed, and a blank
field for the human rating.

Stratification: equal counts across (dataset, condition) cells, and
oversampled at the NLI decision boundary ($0.45 < $ faith $< 0.55$)
where rater agreement matters most.

Output schema (one JSON object per line):
    {
      "id":          0,
      "dataset":     "squad",
      "condition":   "hcpc_v1",
      "question":    "...",
      "ground_truth": "...",
      "answer":      "...",
      "context":     "[truncated retrieved context]",
      "nli_faith":   0.4730,
      "nli_label":   "hallucinated",
      "human_faith": null,        # rater fills in 0/1
      "human_label": null,        # "faithful" | "hallucinated"
      "notes":       null,
    }

After rating, run `analyze_human_eval.py` (separate script) to compute
per-rater accuracy vs NLI and Cohen's kappa.

Inputs:
    results/multidataset/per_query.csv    (preferred)
    results/scaled_headline/per_query.csv (if scaled run completed)
    results/headtohead/per_query.csv      (fallback)

Outputs:
    results/human_eval/samples.jsonl
    results/human_eval/samples.csv         (same data, easier to view)
    results/human_eval/sampling_report.md  (counts per stratum)

Usage:
    python3 experiments/build_human_eval_samples.py --n 100
    python3 experiments/build_human_eval_samples.py --n 200 \\
        --boundary_oversample 0.4
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "results" / "human_eval"

# Inputs are tried in priority order
INPUT_PATHS = [
    ROOT / "results" / "scaled_headline"   / "per_query.csv",
    ROOT / "results" / "multidataset"       / "per_query.csv",
    ROOT / "results" / "headtohead"          / "per_query.csv",
]


def _load() -> pd.DataFrame:
    for p in INPUT_PATHS:
        if p.exists():
            df = pd.read_csv(p)
            print(f"[human-eval] using {p.relative_to(ROOT)} "
                  f"({len(df)} rows)")
            # Normalise required columns
            need = ["dataset", "condition", "question", "ground_truth",
                    "answer", "faithfulness_score", "is_hallucination"]
            for c in need:
                if c not in df.columns:
                    print(f"[human-eval] missing col {c}, skipping {p.name}")
                    df = None
                    break
            if df is not None:
                return df
    raise SystemExit("[human-eval] no usable per_query CSV found")


def _truncate_context(row, max_chars=1200) -> str:
    """We don't have the raw retrieved context in per_query.csv, so we
    return the answer's prefix as a best-effort proxy. This is a known
    limitation: the rater needs the actual passages to validate;
    practically we instruct them to use the question + GT + answer +
    NLI score together as a coarse check."""
    return f"[Context not stored per-query; rater should verify against original {row.get('dataset','?')} passage corpus.]"


def stratified_sample(df: pd.DataFrame, n: int,
                       boundary_oversample: float = 0.3,
                       seed: int = 42) -> pd.DataFrame:
    """Equal counts across (dataset × condition) strata, with extra
    samples at the NLI decision boundary."""
    random.seed(seed)
    df = df.copy().reset_index(drop=True)

    # Stratify across (dataset, condition)
    strata = df.groupby(["dataset", "condition"])
    n_strata = len(strata)
    per_stratum = max(1, n // n_strata)

    picked = []
    for (ds, cond), sub in strata:
        # Boundary oversample
        n_boundary = int(per_stratum * boundary_oversample)
        n_random = per_stratum - n_boundary
        sub = sub.copy()
        sub["dist_to_boundary"] = (sub["faithfulness_score"] - 0.5).abs()

        boundary_picks = sub.nsmallest(min(n_boundary, len(sub)),
                                         "dist_to_boundary")
        remaining = sub.drop(boundary_picks.index)
        random_picks = remaining.sample(min(n_random, len(remaining)),
                                          random_state=seed)
        picked.append(pd.concat([boundary_picks, random_picks]))
    out = pd.concat(picked).head(n).reset_index(drop=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--boundary_oversample", type=float, default=0.3,
                    help="fraction of each stratum drawn from the "
                         "decision boundary (faith near 0.5)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = _load()
    sample = stratified_sample(df, args.n, args.boundary_oversample, args.seed)

    # Build the JSONL records
    records = []
    for i, row in sample.iterrows():
        rec = {
            "id":          int(i),
            "dataset":     row.get("dataset", ""),
            "condition":   row.get("condition", ""),
            "question":    str(row.get("question", "")),
            "ground_truth": str(row.get("ground_truth", "")),
            "answer":      str(row.get("answer", "")),
            "context":     _truncate_context(row),
            "nli_faith":   float(row.get("faithfulness_score", 0.0)),
            "nli_label":   ("hallucinated"
                            if bool(row.get("is_hallucination", False))
                            else "faithful"),
            "human_faith": None,
            "human_label": None,
            "notes":       None,
        }
        records.append(rec)

    jsonl_path = OUT_DIR / "samples.jsonl"
    with jsonl_path.open("w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    print(f"[human-eval] wrote {jsonl_path} ({len(records)} rows)")

    # Mirror CSV
    csv_path = OUT_DIR / "samples.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)
    print(f"[human-eval] wrote {csv_path}")

    # Sampling report
    counts = Counter((r["dataset"], r["condition"], r["nli_label"]) for r in records)
    report = ["# Human-eval sampling report (Phase 7 #6)", "",
              f"Total: {len(records)} samples",
              f"Boundary-oversample fraction: {args.boundary_oversample}",
              f"Seed: {args.seed}", "",
              "## Counts by (dataset, condition, nli_label)", "",
              "| dataset | condition | nli_label | n |",
              "| --- | --- | --- | --- |"]
    for (ds, cond, lbl), n in sorted(counts.items()):
        report.append(f"| {ds} | {cond} | {lbl} | {n} |")
    report += ["", "## Rater protocol",
               "1. Read the question, ground truth, and generated answer.",
               "2. Mark `human_label`: ``faithful`` if the answer is fully ",
               "   supported by the question's standard evidence (the",
               "   rater should be familiar with the dataset); ",
               "   ``hallucinated`` otherwise.",
               "3. Set `human_faith`: 1 if faithful, 0 if hallucinated.",
               "4. Add free-text `notes` for ambiguous cases.",
               "5. After rating: `python3 experiments/analyze_human_eval.py` ",
               "   computes accuracy + Cohen's kappa vs NLI."]
    (OUT_DIR / "sampling_report.md").write_text("\n".join(report))
    print(f"[human-eval] wrote {OUT_DIR / 'sampling_report.md'}")


if __name__ == "__main__":
    main()
