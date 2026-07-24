#!/usr/bin/env python3
"""Select targeted human-annotation cases where scorers disagree.

This is not a broad human-evaluation sampler. It deliberately enriches
for examples where DeBERTa and the RAGAS-style judge disagree, so that
additional labels can stress-test the central scorer-fragility claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


CONDITIONS = ["baseline", "hcpc_v1", "hcpc_v2"]
OUTPUT_COLUMNS = [
    "example_id",
    "query_id",
    "dataset",
    "condition",
    "question",
    "retrieved_context",
    "generated_answer",
    "gold_answer",
    "deberta_score",
    "second_nli_score",
    "ragas_style_score",
    "abs_deberta_ragas_disagreement",
    "disagreement_type",
    "annotator_label",
    "annotator_confidence",
    "annotator_notes",
]


def read_existing_ids(paths: Iterable[str]) -> set[str]:
    ids: set[str] = set()
    for raw in paths:
        path = Path(raw)
        if not path.exists() or path.stat().st_size == 0:
            continue
        if path.suffix == ".jsonl":
            with path.open() as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    if "id" in rec:
                        ids.add(str(rec["id"]))
                    if "example_id" in rec:
                        ids.add(str(rec["example_id"]))
        else:
            df = pd.read_csv(path)
            for col in ["id", "example_id", "source_row"]:
                if col in df.columns:
                    ids.update(df[col].dropna().astype(str))
    return ids


def classify_disagreement(row: pd.Series) -> str:
    deberta = float(row["faith_deberta"])
    ragas = float(row["faith_ragas"])
    threshold_cross = (deberta >= 0.5) != (ragas >= 0.5)
    near_threshold = threshold_cross and min(abs(deberta - 0.5), abs(ragas - 0.5)) <= 0.20
    if near_threshold:
        return "near_threshold_disagreement"
    if deberta > ragas:
        return "deberta_high_ragas_low"
    if ragas > deberta:
        return "ragas_high_deberta_low"
    return "tie"


def prepare_rows(df: pd.DataFrame, used_ids: set[str]) -> pd.DataFrame:
    required = {
        "condition",
        "question",
        "context",
        "answer",
        "faith_deberta",
        "faith_second_nli",
        "faith_ragas",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out = df.reset_index().rename(columns={"index": "source_row"}).copy()
    out = out[out["condition"].isin(CONDITIONS)].copy()
    out = out.dropna(subset=["faith_deberta", "faith_second_nli", "faith_ragas"])
    out["example_id"] = out["source_row"].astype(str)
    if used_ids:
        out = out[~out["example_id"].isin(used_ids)].copy()
    out["abs_deberta_ragas_disagreement"] = (
        out["faith_deberta"].astype(float) - out["faith_ragas"].astype(float)
    ).abs()
    out["disagreement_type"] = out.apply(classify_disagreement, axis=1)
    return out


def round_robin_pick(candidates: pd.DataFrame, target_n: int) -> pd.DataFrame:
    """Pick high-disagreement rows while keeping conditions and types mixed."""
    selected_parts: list[pd.DataFrame] = []
    used_index: set[int] = set()

    buckets: list[tuple[str, str]] = []
    preferred_types = [
        "deberta_high_ragas_low",
        "ragas_high_deberta_low",
        "near_threshold_disagreement",
    ]
    for condition in CONDITIONS:
        for disagreement_type in preferred_types:
            buckets.append((condition, disagreement_type))

    per_bucket = max(1, target_n // max(1, len(buckets)))
    for condition, disagreement_type in buckets:
        sub = candidates[
            candidates["condition"].eq(condition)
            & candidates["disagreement_type"].eq(disagreement_type)
        ].sort_values("abs_deberta_ragas_disagreement", ascending=False)
        take = sub.head(per_bucket)
        selected_parts.append(take)
        used_index.update(take.index.tolist())

    selected = pd.concat(selected_parts, axis=0) if selected_parts else pd.DataFrame()
    remaining_n = target_n - len(selected)
    if remaining_n > 0:
        remaining = candidates[~candidates.index.isin(used_index)].sort_values(
            ["abs_deberta_ragas_disagreement", "condition"],
            ascending=[False, True],
        )
        selected = pd.concat([selected, remaining.head(remaining_n)], axis=0)

    if len(selected) > target_n:
        selected = selected.sort_values(
            ["condition", "disagreement_type", "abs_deberta_ragas_disagreement"],
            ascending=[True, True, False],
        ).head(target_n)
    return selected.sort_values(
        ["condition", "disagreement_type", "abs_deberta_ragas_disagreement"],
        ascending=[True, True, False],
    )


def build_annotation_frame(selected: pd.DataFrame) -> pd.DataFrame:
    dataset = selected["dataset"] if "dataset" in selected.columns else "unknown"
    gold = selected["ground_truth"] if "ground_truth" in selected.columns else ""
    seed = selected["seed"] if "seed" in selected.columns else ""
    query_id = (
        dataset.astype(str)
        + ":"
        + seed.astype(str)
        + ":"
        + selected["source_row"].astype(str)
    )
    out = pd.DataFrame(
        {
            "example_id": selected["example_id"].astype(str),
            "query_id": query_id,
            "dataset": dataset,
            "condition": selected["condition"],
            "question": selected["question"],
            "retrieved_context": selected["context"],
            "generated_answer": selected["answer"],
            "gold_answer": gold,
            "deberta_score": selected["faith_deberta"].astype(float).round(6),
            "second_nli_score": selected["faith_second_nli"].astype(float).round(6),
            "ragas_style_score": selected["faith_ragas"].astype(float).round(6),
            "abs_deberta_ragas_disagreement": selected[
                "abs_deberta_ragas_disagreement"
            ].astype(float).round(6),
            "disagreement_type": selected["disagreement_type"],
            "annotator_label": "",
            "annotator_confidence": "",
            "annotator_notes": "",
        }
    )
    return out[OUTPUT_COLUMNS]


def write_readme(path: Path, annotation: pd.DataFrame, input_path: str, excluded: int) -> None:
    counts_condition = annotation["condition"].value_counts().sort_index()
    counts_type = annotation["disagreement_type"].value_counts().sort_index()

    def bullet_counts(series: pd.Series) -> str:
        return "\n".join(f"- {idx}: {int(val)}" for idx, val in series.items())

    text = f"""# Human Disagreement Expansion

This directory contains a targeted annotation batch for scorer-disagreement
calibration. It is not a broad human-evaluation study.

## Source

- Input rows: `{input_path}`
- Selected file: `annotation_batch_disagreement_100.csv`
- Previously used IDs excluded when available: {excluded}

## Selection Rule

Rows were ranked by the absolute disagreement between the stored DeBERTa score
and the local RAGAS-style score. The sampler then mixed the strongest
disagreements across:

- DeBERTa high / RAGAS-style low
- RAGAS-style high / DeBERTa low
- near-threshold disagreements around the 0.5 hallucination boundary
- baseline, HCPC-v1, and HCPC-v2 conditions

The goal is to stress-test the central metric-fragility claim where automated
scorers disagree most, not to estimate overall population faithfulness.

## Batch Counts by Condition

{bullet_counts(counts_condition)}

## Batch Counts by Disagreement Type

{bullet_counts(counts_type)}

## Annotation Instructions

Annotators should read the question, retrieved context, generated answer, and
gold answer. Label the generated answer against the retrieved context, not
against parametric knowledge.

Use `annotator_label` values:

- `faithful`: every factual claim in the generated answer is supported by the retrieved context.
- `hallucinated`: at least one factual claim is unsupported or contradicted by the retrieved context.
- `unclear`: the context or answer is too ambiguous for a reliable binary decision.

Use `annotator_confidence` as a number from 0 to 1. Use `annotator_notes` for
short rationale or ambiguity notes.

For two-rater annotation, duplicate the three annotator columns with suffixes
such as `_rater1` and `_rater2`, or add an `adjudicated_label` column after
discussion.

## After Annotation

Run:

```bash
python3 scripts/analyze_human_disagreement_labels.py \\
  --input results/human_disagreement_expansion/annotation_batch_disagreement_100.csv
```

The analysis script reports inter-rater agreement when two rater columns exist,
and scorer alignment metrics against an adjudicated or majority label when
labels are available.
"""
    path.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/revision/fix_03/per_query.csv")
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[
            "data/revision/fix_03/human_eval_template.jsonl",
            "results/human_eval/samples.csv",
        ],
    )
    parser.add_argument(
        "--output_dir",
        default="results/human_disagreement_expansion",
    )
    parser.add_argument("--target_n", type=int, default=100)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    used_ids = read_existing_ids(args.exclude)
    candidates = prepare_rows(df, used_ids)
    selected = round_robin_pick(candidates, args.target_n)
    annotation = build_annotation_frame(selected)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "annotation_batch_disagreement_100.csv"
    annotation.to_csv(out_csv, index=False)
    write_readme(out_dir / "README.md", annotation, args.input, excluded=len(used_ids))
    print(f"Wrote {len(annotation)} rows to {out_csv}")


if __name__ == "__main__":
    main()
