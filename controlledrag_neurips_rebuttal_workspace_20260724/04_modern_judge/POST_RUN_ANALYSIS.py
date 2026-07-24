#!/usr/bin/env python3
"""Validate and summarize a later real run; never performs model inference."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from SAMPLE_SELECTION import EXPECTED_SOURCE_SHA256, canonical_digest, sha256_file

CONTRASTS = (
    ("baseline", "hcpc_v1"),
    ("hcpc_v2", "hcpc_v1"),
    ("baseline", "hcpc_v2"),
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {line_number}") from exc
    return records


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot take percentile of empty values")
    position = (len(ordered) - 1) * probability
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    weight = position - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def paired_summary(
    pairs: list[tuple[float, float]], *, seed: int, n_bootstrap: int
) -> dict[str, Any]:
    differences = [left - right for left, right in pairs]
    estimate = statistics.fmean(differences)
    rng = random.Random(seed)
    boot = []
    for _ in range(n_bootstrap):
        sample = [differences[rng.randrange(len(differences))] for _ in differences]
        boot.append(statistics.fmean(sample))
    return {
        "estimate": estimate,
        "ci_lower": percentile(boot, 0.025),
        "ci_upper": percentile(boot, 0.975),
        "n_pairs": len(pairs),
        "n_bootstrap": n_bootstrap,
        "seed": seed,
    }


def analyze(
    manifest: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    results: list[dict[str, Any]],
    *,
    expected_provider: str,
    expected_model: str,
    allowed_routed_via: tuple[str, ...],
    max_fallback_attempts: int = 0,
    n_bootstrap: int = 10_000,
) -> dict[str, Any]:
    manifest_ids = [row["row_id"] for row in manifest]
    if len(manifest_ids) != len(set(manifest_ids)):
        raise ValueError("duplicate row_id in candidate manifest")
    result_ids = [str(row.get("row_id", "")) for row in results]
    if len(result_ids) != len(set(result_ids)):
        raise ValueError("duplicate row_id in final result JSONL")
    extra = sorted(set(result_ids) - set(manifest_ids))
    missing = sorted(set(manifest_ids) - set(result_ids))
    if extra:
        raise ValueError(f"result rows outside manifest: {extra[:3]}")

    by_result = {str(row["row_id"]): row for row in results}
    joined: list[dict[str, Any]] = []
    integrity_errors: list[str] = []
    for manifest_row in manifest:
        source_index = int(manifest_row["source_row_index"])
        source = source_rows[source_index]
        result = by_result.get(manifest_row["row_id"])
        if canonical_digest(
            source,
            (
                "question",
                "ground_truth",
                "condition",
                "answer",
                "context",
                "dataset",
                "seed",
                "model",
            ),
        ) != manifest_row["input_digest"]:
            integrity_errors.append(f"input digest mismatch: {manifest_row['row_id']}")
            continue
        if result is None:
            continue
        if result.get("input_digest") != manifest_row["input_digest"]:
            integrity_errors.append(f"result digest mismatch: {manifest_row['row_id']}")
        if result.get("requested_provider") != expected_provider:
            integrity_errors.append(f"provider mismatch: {manifest_row['row_id']}")
        if result.get("requested_model") != expected_model:
            integrity_errors.append(f"requested model mismatch: {manifest_row['row_id']}")
        if result.get("returned_model") != expected_model:
            integrity_errors.append(f"returned model mismatch: {manifest_row['row_id']}")
        if result.get("x_routed_via") not in allowed_routed_via:
            integrity_errors.append(f"route mismatch: {manifest_row['row_id']}")
        try:
            fallback_attempts = int(result.get("x_fallback_attempts"))
        except (TypeError, ValueError):
            integrity_errors.append(
                f"invalid fallback count: {manifest_row['row_id']}"
            )
        else:
            if fallback_attempts > max_fallback_attempts:
                integrity_errors.append(
                    f"fallback limit exceeded: {manifest_row['row_id']}"
                )
        parsed = result.get("parsed_output")
        if result.get("status") == "ok" and isinstance(parsed, dict):
            joined.append(
                {
                    "row_id": manifest_row["row_id"],
                    "pair_id": manifest_row["pair_id"],
                    "condition": manifest_row["condition"],
                    "score": float(parsed["score"]),
                    "label": str(parsed["label"]),
                }
            )

    grouped_scores: dict[str, list[float]] = defaultdict(list)
    labels: dict[str, Counter[str]] = defaultdict(Counter)
    pair_scores: dict[str, dict[str, float]] = defaultdict(dict)
    for row in joined:
        grouped_scores[row["condition"]].append(row["score"])
        labels[row["condition"]][row["label"]] += 1
        pair_scores[row["pair_id"]][row["condition"]] = row["score"]

    contrasts: dict[str, Any] = {}
    for contrast_index, (left, right) in enumerate(CONTRASTS):
        pairs = [
            (scores[left], scores[right])
            for scores in pair_scores.values()
            if left in scores and right in scores
        ]
        if pairs:
            contrasts[f"{left}_minus_{right}"] = paired_summary(
                pairs,
                seed=20260724 + contrast_index,
                n_bootstrap=n_bootstrap,
            )

    status_counts = Counter(str(row.get("status", "")) for row in results)
    return {
        "analysis_schema_version": "1.0",
        "scientifically_valid": (
            not integrity_errors
            and not missing
            and status_counts.get("routing_rejected", 0) == 0
            and status_counts.get("provider_error", 0) == 0
        ),
        "manifest_rows": len(manifest),
        "result_rows": len(results),
        "accepted_rows": len(joined),
        "missing_row_ids": missing,
        "integrity_errors": integrity_errors,
        "status_counts": dict(status_counts),
        "condition_means": {
            condition: statistics.fmean(scores)
            for condition, scores in grouped_scores.items()
        },
        "label_counts": {
            condition: dict(counter) for condition, counter in labels.items()
        },
        "paired_contrasts": contrasts,
        "interpretation": (
            "Fixed-output rescoring sensitivity only; not fresh retrieval/generation "
            "and not evidence of a universally correct judge."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--expected-provider", required=True)
    parser.add_argument("--expected-model", required=True)
    parser.add_argument("--allowed-routed-via", action="append", required=True)
    parser.add_argument("--max-fallback-attempts", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sha256_file(args.source) != EXPECTED_SOURCE_SHA256:
        raise ValueError("source SHA mismatch")
    summary = analyze(
        read_csv(args.manifest),
        read_csv(args.source),
        read_jsonl(args.results),
        expected_provider=args.expected_provider,
        expected_model=args.expected_model,
        allowed_routed_via=tuple(args.allowed_routed_via),
        max_fallback_attempts=args.max_fallback_attempts,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
