"""
Fix 15: small long-form/synthesis appendix stress test summary.

This pass does not rerun generation by default. It packages the existing
free-compute long-form outputs (`results/longform/`) into revision-scoped
trace artifacts and a concise supplement-ready interpretation.

Primary command:

    python3 experiments/fix_15_longform_stress.py

Outputs:
    data/revision/fix_15/longform_stress_per_query.csv
    results/revision/fix_15/longform_stress_summary.csv
    results/revision/fix_15/longform_stress_report.md
    source_tables/longform_stress_summary.csv
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd

from experiments.revision_utils import ensure_dirs


OUT_DATA = Path("data/revision/fix_15")
OUT_RESULTS = Path("results/revision/fix_15")
OUT_SOURCE = Path("source_tables")


def safe_read(path: Path) -> pd.DataFrame:
    if path.exists() and path.stat().st_size:
        return pd.read_csv(path)
    return pd.DataFrame()


def build_summary(per_query: pd.DataFrame, summary: pd.DataFrame, paradox: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for _, row in summary.iterrows():
        rows.append(
            {
                "dataset": row["dataset"],
                "model": row["model"],
                "condition": row["condition"],
                "n_queries": int(row["n_queries"]),
                "span_faith": row["span_faith"],
                "claim_faith": row["claim_faith"],
                "unsupported_rate": row["unsupported_rate"],
                "rouge_l": row["rouge_l"],
                "halluc_long": row["halluc_long"],
                "refine_rate": row["refine_rate"],
                "ccs": row.get("ccs", np.nan),
                "source": "results/longform/summary.csv",
            }
        )
    out = pd.DataFrame(rows)
    if not paradox.empty:
        keep = paradox[
            [
                "dataset",
                "model",
                "span_paradox_drop",
                "claim_paradox_drop",
                "unsupported_rate_base",
                "unsupported_rate_v1",
                "unsupported_rate_v2",
            ]
        ].copy()
        keep["condition"] = "contrast"
        keep["source"] = "results/longform/paradox_longform.csv"
        out = pd.concat([out, keep], ignore_index=True, sort=False)
    return out


def write_report(summary: pd.DataFrame, per_query: pd.DataFrame, out_path: Path) -> None:
    contrast = summary[summary["condition"].eq("contrast")]
    aggregate = summary[~summary["condition"].eq("contrast")]
    n_examples = int(per_query[["dataset", "question"]].drop_duplicates().shape[0]) if not per_query.empty else 0
    lines = [
        "# Fix 15 - long-form/synthesis stress test",
        "",
        f"Source: existing `results/longform/` run, {n_examples} distinct long-form questions.",
        "This is exploratory appendix evidence only; it is not a broad long-form validation.",
        "",
        "## Aggregated condition metrics",
        "",
        aggregate.to_markdown(index=False) if not aggregate.empty else "(no aggregate rows)",
        "",
        "## Contrast rows",
        "",
        contrast.to_markdown(index=False) if not contrast.empty else "(no contrast rows)",
        "",
        "## Compact interpretation",
        "",
        "The small stress test shows that scorer and condition sensitivity can appear outside short-answer QA, but the sample is too small and dataset-specific for broad claims.",
        "It belongs in the supplement as a scope probe, not as a central result.",
        "",
    ]
    out_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per_query", default="results/longform/per_query.csv")
    parser.add_argument("--summary", default="results/longform/summary.csv")
    parser.add_argument("--paradox", default="results/longform/paradox_longform.csv")
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS, OUT_SOURCE)
    per_query = safe_read(Path(args.per_query))
    summary = safe_read(Path(args.summary))
    paradox = safe_read(Path(args.paradox))
    if per_query.empty or summary.empty:
        raise FileNotFoundError("Expected existing long-form artifacts under results/longform/")

    per_query.to_csv(OUT_DATA / "longform_stress_per_query.csv", index=False)
    out = build_summary(per_query, summary, paradox)
    out.to_csv(OUT_RESULTS / "longform_stress_summary.csv", index=False)
    out.to_csv(OUT_SOURCE / "longform_stress_summary.csv", index=False)
    write_report(out, per_query, OUT_RESULTS / "longform_stress_report.md")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
