#!/usr/bin/env python3
"""Strict post-run validity analysis; never performs model inference."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from prompt_rendering import render_prompt
from provider_adapter import derive_label, validate_record_shape
from run_config import load_and_validate_config
from run_state import atomic_write_json, attempt_key, terminal_state
from SAMPLE_SELECTION import IDENTITY_FIELDS, canonical_digest, sha256_file

CONTRASTS = (
    ("baseline", "hcpc_v1"),
    ("hcpc_v2", "hcpc_v1"),
    ("baseline", "hcpc_v2"),
)
FAILURE_STATUSES = {
    "parse_error",
    "provider_error",
    "routing_rejected",
    "integrity_error",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    data = path.read_bytes()
    if data and not data.endswith(b"\n"):
        raise ValueError(f"partial JSONL tail: {path}")
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(data.splitlines(), start=1):
        if not raw:
            raise ValueError(f"blank JSONL line {line_number}: {path}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at line {line_number}: {path}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"JSONL line {line_number} is not an object: {path}")
        records.append(value)
    return records


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
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
    boot = [
        statistics.fmean([differences[rng.randrange(len(differences))] for _ in differences])
        for _ in range(n_bootstrap)
    ]
    return {
        "estimate": estimate,
        "ci_lower": percentile(boot, 0.025),
        "ci_upper": percentile(boot, 0.975),
        "n_pairs": len(pairs),
        "n_bootstrap": n_bootstrap,
        "seed": seed,
    }


def _duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def analyze(
    manifest: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    results: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
    *,
    config: Mapping[str, Any],
    actual_source_sha256: str,
    actual_manifest_sha256: str,
    expected_prompt_digests: Mapping[str, str],
    n_bootstrap: int = 10_000,
) -> dict[str, Any]:
    gate_failures: list[str] = []
    integrity_errors: list[str] = []
    manifest_ids = [str(row.get("row_id", "")) for row in manifest]
    result_ids = [str(row.get("row_id", "")) for row in results]
    duplicate_manifest_rows = _duplicates(manifest_ids)
    duplicate_result_rows = _duplicates(result_ids)
    extra_rows = sorted(set(result_ids) - set(manifest_ids))
    missing_rows = sorted(set(manifest_ids) - set(result_ids))
    if duplicate_manifest_rows:
        gate_failures.append("duplicate_manifest_rows")
    if duplicate_result_rows:
        gate_failures.append("duplicate_final_rows")
    if extra_rows:
        gate_failures.append("extra_final_rows")
    if missing_rows:
        gate_failures.append("missing_final_rows")
    if actual_source_sha256 != config["source_sha256"]:
        gate_failures.append("source_hash_mismatch")
    if actual_manifest_sha256 != config["candidate_manifest_sha256"]:
        gate_failures.append("manifest_hash_mismatch")

    by_result: dict[str, dict[str, Any]] = {}
    for candidate_result in results:
        by_result.setdefault(
            str(candidate_result.get("row_id", "")), candidate_result
        )
        try:
            validate_record_shape(candidate_result)
        except Exception as exc:
            integrity_errors.append(
                f"final record schema failure {candidate_result.get('row_id', '')}: {type(exc).__name__}"
            )
    for attempt in attempts:
        try:
            validate_record_shape(attempt)
        except Exception as exc:
            integrity_errors.append(
                f"attempt record schema failure {attempt.get('row_id', '')}: {type(exc).__name__}"
            )
    by_manifest = {str(row.get("row_id", "")): row for row in manifest}
    accepted: list[dict[str, Any]] = []
    routing_consistent = True
    prompt_consistent = True
    model_consistent = True
    manifest_consistent = True
    source_consistent = actual_source_sha256 == config["source_sha256"]

    for row_id, manifest_row in by_manifest.items():
        try:
            source = source_rows[int(manifest_row["source_row_index"])]
        except (IndexError, KeyError, TypeError, ValueError):
            integrity_errors.append(f"invalid source index: {row_id}")
            source_consistent = False
            continue
        if canonical_digest(source, IDENTITY_FIELDS) != manifest_row.get("input_digest"):
            integrity_errors.append(f"source input digest mismatch: {row_id}")
            source_consistent = False
        result_record = by_result.get(row_id)
        if result_record is None:
            continue
        for field in ("pair_id", "condition", "input_digest"):
            if result_record.get(field) != manifest_row.get(field):
                integrity_errors.append(f"manifest {field} mismatch: {row_id}")
                manifest_consistent = False
        if result_record.get("prompt_digest") != expected_prompt_digests.get(row_id):
            integrity_errors.append(f"prompt digest mismatch: {row_id}")
            prompt_consistent = False
        if (
            result_record.get("prompt_version") != config["prompt_version"]
            or result_record.get("parser_version") != config["parser_version"]
            or result_record.get("prompt_transport") != config["prompt_transport"]
        ):
            integrity_errors.append(f"prompt/parser version mismatch: {row_id}")
            prompt_consistent = False
        if (
            result_record.get("requested_provider") != config["provider"]
            or result_record.get("requested_model") != config["model"]
            or result_record.get("model_revision") != config["model_revision"]
        ):
            integrity_errors.append(f"requested model/provider mismatch: {row_id}")
            model_consistent = False
        status = str(result_record.get("status", ""))
        if status in {"ok", "parse_error", "routing_rejected"}:
            if result_record.get("returned_model") not in config["allowed_returned_models"]:
                integrity_errors.append(f"returned model mismatch: {row_id}")
                model_consistent = False
            if result_record.get("x_routed_via") not in config["allowed_routed_via"]:
                integrity_errors.append(f"route mismatch: {row_id}")
                routing_consistent = False
            fallback = result_record.get("x_fallback_attempts")
            if not isinstance(fallback, int) or fallback > config["allow_fallback_attempts"]:
                integrity_errors.append(f"fallback mismatch: {row_id}")
                routing_consistent = False
        if result_record.get("terminal") is not True:
            integrity_errors.append(f"nonterminal record in final output: {row_id}")
        if status == "ok":
            score = result_record.get("parsed_score")
            label = result_record.get("derived_label")
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                integrity_errors.append(f"invalid parsed score: {row_id}")
                continue
            score_value = float(score)
            expected_label = derive_label(score_value)
            if label != expected_label:
                integrity_errors.append(f"derived label mismatch: {row_id}")
                continue
            accepted.append(
                {
                    "row_id": row_id,
                    "pair_id": manifest_row["pair_id"],
                    "condition": manifest_row["condition"],
                    "score": score_value,
                    "label": str(label),
                }
            )

    attempt_keys: list[tuple[str, str, int]] = []
    malformed_attempts = 0
    for record in attempts:
        try:
            attempt_keys.append(attempt_key(record))
        except Exception:
            malformed_attempts += 1
    duplicate_attempt_keys = [
        list(key) for key, count in Counter(attempt_keys).items() if count > 1
    ]
    attempts_by_row: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in attempts:
        attempts_by_row[str(record.get("row_id", ""))].append(record)
    terminal_attempt_consistent = not malformed_attempts and not duplicate_attempt_keys
    retry_count = 0
    exhausted_retry_count = 0
    exceeded_retry_rows: list[str] = []
    for row_id, row_attempts in attempts_by_row.items():
        ordered = sorted(row_attempts, key=lambda item: int(item.get("attempt", 0)))
        retry_count += max(0, len(ordered) - 1)
        numbers = [int(item.get("attempt", 0)) for item in ordered]
        if numbers != list(range(1, len(numbers) + 1)):
            terminal_attempt_consistent = False
        if any(int(item.get("attempt", 0)) > int(item.get("max_attempts", 0)) for item in ordered):
            exceeded_retry_rows.append(row_id)
            terminal_attempt_consistent = False
        terminal_positions = [
            index
            for index, item in enumerate(ordered)
            if bool(item.get("terminal"))
        ]
        if terminal_positions and terminal_positions != [len(ordered) - 1]:
            terminal_attempt_consistent = False
        final = by_result.get(row_id)
        if final is not None:
            if not ordered or ordered[-1] != final:
                terminal_attempt_consistent = False
            else:
                try:
                    if not terminal_state(ordered[-1], attempt_count=len(ordered)):
                        terminal_attempt_consistent = False
                except Exception:
                    terminal_attempt_consistent = False
        if ordered:
            last = ordered[-1]
            if (
                last.get("status") in {"parse_error", "provider_error"}
                and int(last.get("attempt", 0)) >= int(last.get("max_attempts", 0))
            ):
                exhausted_retry_count += 1
    if set(attempts_by_row) - set(manifest_ids):
        terminal_attempt_consistent = False
    if not terminal_attempt_consistent:
        gate_failures.append("terminal_attempt_inconsistency")

    status_counts = Counter(str(row.get("status", "")) for row in results)
    unknown_statuses = sorted(set(status_counts) - (FAILURE_STATUSES | {"ok"}))
    if unknown_statuses:
        gate_failures.append("unknown_terminal_status")
    manifest_count = len(manifest)
    terminal_count = sum(bool(row.get("terminal")) for row in results)
    ok_count = status_counts.get("ok", 0)
    parse_count = status_counts.get("parse_error", 0)
    provider_count = status_counts.get("provider_error", 0)
    routing_count = status_counts.get("routing_rejected", 0)
    integrity_count = status_counts.get("integrity_error", 0)
    parse_rate = parse_count / manifest_count if manifest_count else 1.0
    provider_rate = provider_count / manifest_count if manifest_count else 1.0
    overall_error_rate = (manifest_count - ok_count) / manifest_count if manifest_count else 1.0
    condition_totals = Counter(row["condition"] for row in manifest)
    condition_ok = Counter(row["condition"] for row in accepted)
    condition_error_rates = {
        condition: (
            (condition_totals[condition] - condition_ok[condition]) / condition_totals[condition]
            if condition_totals[condition]
            else 1.0
        )
        for condition in sorted(condition_totals)
    }
    condition_difference = (
        max(condition_error_rates.values()) - min(condition_error_rates.values())
        if condition_error_rates
        else 1.0
    )

    if parse_rate > config["max_parse_error_rate"]:
        gate_failures.append("parse_error_rate_exceeded")
    if provider_rate > config["max_provider_error_rate"]:
        gate_failures.append("provider_error_rate_exceeded")
    if condition_difference > config["max_condition_error_rate_difference"]:
        gate_failures.append("condition_error_rate_difference_exceeded")
    if config["require_all_manifest_rows_terminal"] and terminal_count != manifest_count:
        gate_failures.append("not_all_manifest_rows_terminal")
    if config["require_all_manifest_rows_ok"] and ok_count != manifest_count:
        gate_failures.append("not_all_manifest_rows_ok")
    if routing_count:
        gate_failures.append("routing_rejection_present")
    if integrity_count or integrity_errors:
        gate_failures.append("integrity_failure_present")
    if not routing_consistent:
        gate_failures.append("routing_inconsistent")
    if not model_consistent:
        gate_failures.append("model_provider_inconsistent")
    if not prompt_consistent:
        gate_failures.append("prompt_inconsistent")
    if not manifest_consistent:
        gate_failures.append("manifest_inconsistent")
    if not source_consistent:
        gate_failures.append("source_inconsistent")

    scores_by_pair: dict[str, dict[str, float]] = defaultdict(dict)
    labels_by_condition: dict[str, Counter[str]] = defaultdict(Counter)
    scores_by_condition: dict[str, list[float]] = defaultdict(list)
    for row in accepted:
        scores_by_pair[row["pair_id"]][row["condition"]] = row["score"]
        scores_by_condition[row["condition"]].append(row["score"])
        labels_by_condition[row["condition"]][row["label"]] += 1

    manifest_pairs_by_condition: dict[str, set[str]] = defaultdict(set)
    for row in manifest:
        manifest_pairs_by_condition[row["condition"]].add(row["pair_id"])
    contrasts: dict[str, Any] = {}
    primary_key = "baseline_minus_hcpc_v1"
    for contrast_index, (left, right) in enumerate(CONTRASTS):
        key = f"{left}_minus_{right}"
        candidate_pair_ids = manifest_pairs_by_condition[left] & manifest_pairs_by_condition[right]
        successful_pair_ids = {
            pair_id
            for pair_id in candidate_pair_ids
            if left in scores_by_pair[pair_id] and right in scores_by_pair[pair_id]
        }
        excluded_ids = sorted(candidate_pair_ids - successful_pair_ids)
        causes: Counter[str] = Counter()
        left_only_failures = 0
        right_only_failures = 0
        for pair_id in excluded_ids:
            pair_rows = {
                row["condition"]: by_result.get(row["row_id"])
                for row in manifest
                if row["pair_id"] == pair_id and row["condition"] in {left, right}
            }
            left_record = pair_rows.get(left)
            right_record = pair_rows.get(right)
            left_status = str(left_record.get("status")) if left_record else "missing"
            right_status = str(right_record.get("status")) if right_record else "missing"
            causes[f"{left_status}|{right_status}"] += 1
            if left_status != "ok" and right_status == "ok":
                left_only_failures += 1
            if right_status != "ok" and left_status == "ok":
                right_only_failures += 1
        minimum = config["min_primary_complete_pairs"] if key == primary_key else 0
        passes_minimum = len(successful_pair_ids) >= minimum
        pair_values = [
            (scores_by_pair[pair_id][left], scores_by_pair[pair_id][right])
            for pair_id in sorted(successful_pair_ids)
        ]
        entry: dict[str, Any] = {
            "candidate_pairs": len(candidate_pair_ids),
            "complete_successful_pairs": len(successful_pair_ids),
            "excluded_pairs": len(excluded_ids),
            "exclusion_causes": dict(causes),
            "condition_asymmetry": {
                f"{left}_only_failure": left_only_failures,
                f"{right}_only_failure": right_only_failures,
            },
            "minimum_required": minimum,
            "passes_minimum": passes_minimum,
        }
        if pair_values:
            entry["estimate"] = paired_summary(
                pair_values,
                seed=20260724 + contrast_index,
                n_bootstrap=n_bootstrap,
            )
        contrasts[key] = entry
        if key == primary_key and not passes_minimum:
            gate_failures.append("insufficient_primary_complete_pairs")

    gate_failures = sorted(set(gate_failures))
    scientifically_valid = not gate_failures
    return {
        "analysis_schema_version": "2.0",
        "scientifically_valid": scientifically_valid,
        "rebuttal_safe_interpretation": (
            "VALID_BOUNDED_FIXED_OUTPUT_SENSITIVITY"
            if scientifically_valid
            else "NOT_REBUTTAL_SAFE_STRICT_GATE_FAILURE"
        ),
        "gate_failures": gate_failures,
        "manifest_rows": manifest_count,
        "terminal_result_rows": terminal_count,
        "accepted_ok_rows": ok_count,
        "missing_row_ids": missing_rows,
        "extra_row_ids": extra_rows,
        "duplicate_manifest_row_ids": duplicate_manifest_rows,
        "duplicate_final_row_ids": duplicate_result_rows,
        "duplicate_attempt_keys": duplicate_attempt_keys,
        "malformed_attempt_count": malformed_attempts,
        "status_counts": dict(status_counts),
        "parse_errors": parse_count,
        "provider_errors": provider_count,
        "routing_rejections": routing_count,
        "configuration_failures": 0,
        "integrity_failures": integrity_count + len(integrity_errors),
        "integrity_errors": integrity_errors,
        "retry_count": retry_count,
        "exhausted_retry_count": exhausted_retry_count,
        "exceeded_retry_rows": sorted(exceeded_retry_rows),
        "overall_error_rate": overall_error_rate,
        "parse_error_rate": parse_rate,
        "provider_error_rate": provider_rate,
        "condition_error_rates": condition_error_rates,
        "max_condition_error_rate_difference": condition_difference,
        "terminal_attempt_consistent": terminal_attempt_consistent,
        "prompt_hash_consistent": prompt_consistent,
        "source_hash_consistent": source_consistent,
        "model_provider_routing_consistent": (
            model_consistent and routing_consistent
        ),
        "manifest_consistent": manifest_consistent,
        "condition_means": {
            condition: statistics.fmean(scores)
            for condition, scores in scores_by_condition.items()
        },
        "derived_label_counts": {
            condition: dict(counter)
            for condition, counter in labels_by_condition.items()
        },
        "paired_contrasts": contrasts,
        "primary_complete_pair_count": contrasts[primary_key]["complete_successful_pairs"],
        "minimum_primary_complete_pairs": config["min_primary_complete_pairs"],
        "interpretation_limit": (
            "Fixed-output rescoring sensitivity only; not fresh retrieval/generation "
            "and not evidence of a universally correct judge."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--attempts", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--template", type=Path, default=Path(__file__).with_name("PROMPT_TEMPLATE.md"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = load_and_validate_config(args.config)
    manifest = read_csv(args.manifest)
    source_rows = read_csv(args.source)
    expected_prompt_digests = {}
    for manifest_row in manifest:
        source = source_rows[int(manifest_row["source_row_index"])]
        expected_prompt_digests[manifest_row["row_id"]] = render_prompt(
            args.template,
            question=source["question"],
            context=source["context"],
            answer=source["answer"],
            transport=config["prompt_transport"],
        ).digest
    summary = analyze(
        manifest,
        source_rows,
        read_jsonl(args.results),
        read_jsonl(args.attempts),
        config=config,
        actual_source_sha256=sha256_file(args.source),
        actual_manifest_sha256=sha256_file(args.manifest),
        expected_prompt_digests=expected_prompt_digests,
    )
    atomic_write_json(args.output, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
