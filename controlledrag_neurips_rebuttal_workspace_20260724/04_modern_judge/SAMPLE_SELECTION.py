#!/usr/bin/env python3
"""Build deterministic, text-free candidate manifests from the fixed n=600 CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

EXPECTED_SOURCE_SHA256 = (
    "78348a4a786434fbf5aa42e1179f7c81aae7695eaee4e876d145aa3cb1a575f4"
)
SALT = "controlledrag-modern-judge-v1"
SIZES = (300, 400, 500, 600)
CONDITIONS = ("baseline", "hcpc_v1", "hcpc_v2")
IDENTITY_FIELDS = (
    "question",
    "ground_truth",
    "condition",
    "answer",
    "context",
    "dataset",
    "seed",
    "model",
)
PAIR_FIELDS = ("question", "dataset", "seed", "model")
MANIFEST_FIELDS = (
    "candidate_size",
    "candidate_position",
    "source_row_index",
    "row_id",
    "pair_id",
    "input_digest",
    "condition",
    "dataset",
    "seed",
    "generator_model",
    "source_sha256",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_digest(row: dict[str, str], fields: Iterable[str]) -> str:
    payload = "\x1f".join(row.get(field, "") for field in fields)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_rows(path: Path) -> list[dict[str, str]]:
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            f"source SHA mismatch: expected {EXPECTED_SOURCE_SHA256}, got {actual_sha}"
        )
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 600:
        raise ValueError(f"expected 600 rows, found {len(rows)}")
    missing = sorted(set(IDENTITY_FIELDS) - set(rows[0]))
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    counts = Counter(row["condition"] for row in rows)
    if counts != Counter({condition: 200 for condition in CONDITIONS}):
        raise ValueError(f"unexpected condition counts: {dict(counts)}")
    return rows


def prepare_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    seen: set[str] = set()
    for source_index, row in enumerate(rows):
        input_digest = canonical_digest(row, IDENTITY_FIELDS)
        row_id = f"crj_{input_digest[:24]}"
        if row_id in seen:
            raise ValueError(f"duplicate stable row ID: {row_id}")
        seen.add(row_id)
        pair_digest = canonical_digest(row, PAIR_FIELDS)
        pair_id = f"crjp_{pair_digest[:24]}"
        group = grouped.setdefault(
            pair_id,
            {
                "pair_id": pair_id,
                "_rank_key": hashlib.sha256(
                    f"{SALT}:{pair_id}".encode("utf-8")
                ).hexdigest(),
                "rows": {},
            },
        )
        group_rows = group["rows"]
        assert isinstance(group_rows, dict)
        if row["condition"] in group_rows:
            raise ValueError(
                f"duplicate condition {row['condition']} for pair {pair_id}"
            )
        group_rows[row["condition"]] = {
                "source_row_index": str(source_index),
                "row_id": row_id,
                "pair_id": pair_id,
                "input_digest": input_digest,
                "condition": row["condition"],
                "dataset": row["dataset"],
                "seed": row["seed"],
                "generator_model": row["model"],
            }
    if len(grouped) != 200:
        raise ValueError(f"expected 200 query groups, found {len(grouped)}")
    for pair_id, group in grouped.items():
        group_rows = group["rows"]
        assert isinstance(group_rows, dict)
        if set(group_rows) != set(CONDITIONS):
            raise ValueError(f"incomplete condition set for pair {pair_id}")
    return sorted(
        grouped.values(), key=lambda group: (str(group["_rank_key"]), str(group["pair_id"]))
    )


def select_candidate(groups: list[dict[str, object]], size: int) -> list[dict[str, str]]:
    chosen: list[dict[str, str]] = []
    complete_groups, remainder = divmod(size, len(CONDITIONS))
    for group in groups[:complete_groups]:
        group_rows = group["rows"]
        assert isinstance(group_rows, dict)
        chosen.extend(group_rows[condition] for condition in CONDITIONS)
    if remainder:
        group_rows = groups[complete_groups]["rows"]
        assert isinstance(group_rows, dict)
        chosen.extend(group_rows[condition] for condition in CONDITIONS[:remainder])
    output = []
    for position, item in enumerate(chosen):
        output.append(
            {
                "candidate_size": str(size),
                "candidate_position": str(position),
                "source_row_index": item["source_row_index"],
                "row_id": item["row_id"],
                "pair_id": item["pair_id"],
                "input_digest": item["input_digest"],
                "condition": item["condition"],
                "dataset": item["dataset"],
                "seed": item["seed"],
                "generator_model": item["generator_model"],
                "source_sha256": EXPECTED_SOURCE_SHA256,
            }
        )
    if len(output) != size or len({row["row_id"] for row in output}) != size:
        raise AssertionError("candidate size or uniqueness invariant failed")
    return output


def write_candidates(input_path: Path, output_dir: Path) -> dict[str, object]:
    rows = load_rows(input_path)
    groups = prepare_rows(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_records: list[dict[str, object]] = []
    previous: set[str] = set()
    for size in SIZES:
        candidate = select_candidate(groups, size)
        current = {row["row_id"] for row in candidate}
        if not previous.issubset(current):
            raise AssertionError(f"candidate n={size} is not nested")
        previous = current
        path = output_dir / f"candidate_n{size}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(candidate)
        candidate_records.append(
            {
                "size": size,
                "file": path.name,
                "sha256": sha256_file(path),
                "condition_counts": dict(Counter(row["condition"] for row in candidate)),
                "complete_three_condition_pairs": size // 3,
                "complete_baseline_hcpc_v1_pairs": (size + 1) // 3,
                "unique_row_ids": len(current),
                "contains_raw_text": False,
            }
        )
    index = {
        "schema_version": "1.0",
        "selection_salt": SALT,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "source_rows": len(rows),
        "candidates_are_nested": True,
        "candidate_records": candidate_records,
    }
    index_path = output_dir / "candidates_index.json"
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    index = write_candidates(args.input, args.output_dir)
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
