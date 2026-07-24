"""
experiments/analyze_human_eval.py — Phase 7 #6 (companion analyser)
====================================================================

Read back the human-rated samples.jsonl (after the rater fills in the
human_faith / human_label fields) and compute:

  - rater accuracy vs the NLI label
  - Cohen's kappa
  - per-stratum agreement
  - confusion matrix

If the rater agrees with NLI in say >85% of cases and kappa > 0.6,
the NLI score is a defensible faithfulness proxy. The honest caveat
in the paper is that we have a SINGLE rater (the author); the report
is to be read as a sanity check, not a multi-rater inter-annotator
study.

Usage:
    python3 experiments/analyze_human_eval.py
    python3 experiments/analyze_human_eval.py --rated_jsonl results/human_eval/samples_rated.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "results" / "human_eval" / "samples.jsonl"


def cohens_kappa(a, b):
    """Two-rater Cohen's kappa (binary or multi-class)."""
    from collections import Counter
    if len(a) != len(b):
        raise ValueError("rater vectors must be same length")
    n = len(a)
    if n == 0: return float("nan")
    labels = sorted(set(a) | set(b))
    obs_agree = sum(1 for x, y in zip(a, b) if x == y) / n
    a_counts = Counter(a)
    b_counts = Counter(b)
    exp_agree = sum((a_counts[L] / n) * (b_counts[L] / n) for L in labels)
    if exp_agree == 1.0: return 1.0
    return (obs_agree - exp_agree) / (1.0 - exp_agree)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rated_jsonl", default=str(DEFAULT_PATH))
    args = ap.parse_args()

    path = Path(args.rated_jsonl)
    if not path.exists():
        raise SystemExit(f"[human-eval] not found: {path}")

    records = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    df = pd.DataFrame(records)

    rated = df.dropna(subset=["human_label"])
    if rated.empty:
        raise SystemExit(f"[human-eval] no rated rows in {path} "
                          "(human_label is null in all of them).")
    print(f"[human-eval] {len(rated)} rated rows of {len(df)} total")

    # Compare NLI vs human label
    nli_lbl = rated["nli_label"].astype(str).tolist()
    hum_lbl = rated["human_label"].astype(str).tolist()

    n_agree = sum(1 for a, b in zip(nli_lbl, hum_lbl) if a == b)
    accuracy = n_agree / len(rated)
    kappa = cohens_kappa(nli_lbl, hum_lbl)

    print(f"[human-eval] accuracy (NLI vs human) = {accuracy:.4f}")
    print(f"[human-eval] Cohen's kappa             = {kappa:.4f}")

    # Confusion matrix
    cm_counter = Counter((a, b) for a, b in zip(nli_lbl, hum_lbl))
    print(f"\n[human-eval] confusion matrix (NLI label × human label):")
    labels = sorted(set(nli_lbl) | set(hum_lbl))
    header = "NLI \\ human"
    print(f"{header:>14}  " + "  ".join(f"{L:>13}" for L in labels))
    for a in labels:
        row = "  ".join(f"{cm_counter[(a, b)]:>13}" for b in labels)
        print(f"{a:>14}  " + row)

    # Per-stratum agreement
    rated["agree"] = [a == b for a, b in zip(nli_lbl, hum_lbl)]
    by_stratum = rated.groupby(["dataset", "condition"]).agg(
        n=("id", "count"),
        accuracy=("agree", "mean"),
    ).reset_index()
    print(f"\n[human-eval] per-stratum agreement:")
    print(by_stratum.to_string(index=False))

    out_dir = path.parent
    pd.DataFrame([{
        "n_rated":   len(rated),
        "accuracy":  round(float(accuracy), 4),
        "kappa":     round(float(kappa), 4),
    }]).to_csv(out_dir / "agreement.csv", index=False)
    by_stratum.to_csv(out_dir / "agreement_by_stratum.csv", index=False)

    md = ["# Human-eval agreement (Phase 7 #6)", "",
          f"Single-rater (author) validation of NLI faithfulness ",
          f"on {len(rated)} stratified samples.", "",
          f"- **Accuracy (NLI ↔ human)**: {accuracy:.4f}",
          f"- **Cohen's kappa**: {kappa:.4f}", "",
          "## Per-stratum agreement", "",
          by_stratum.to_markdown(index=False), "",
          "## Confusion matrix",
          ""] + [
              "| NLI \\\\ human | " + " | ".join(labels) + " |",
              "| --- | " + " | ".join(["---"] * len(labels)) + " |",
          ] + [
              "| " + a + " | " + " | ".join(str(cm_counter[(a, b)]) for b in labels) + " |"
              for a in labels
          ] + ["",
                "## Caveat", "",
                "Single-rater study (author). To be read as a sanity check, ",
                "not a multi-rater inter-annotator agreement (IAA) study. ",
                "Multi-rater IAA via Prolific is deferred (per limitations)."]
    (out_dir / "agreement_report.md").write_text("\n".join(md))
    print(f"\n[human-eval] outputs -> {out_dir.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
