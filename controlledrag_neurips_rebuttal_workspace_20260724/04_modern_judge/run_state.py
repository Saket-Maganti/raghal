"""Retry/resume state and atomic persistence for judge attempts."""

from __future__ import annotations

import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from errors import IntegrityError

RETRYABLE_STATUSES = {"parse_error", "provider_error"}
ALWAYS_TERMINAL_STATUSES = {"ok", "routing_rejected", "integrity_error"}
KNOWN_STATUSES = RETRYABLE_STATUSES | ALWAYS_TERMINAL_STATUSES


def attempt_key(record: Mapping[str, Any]) -> tuple[str, str, int]:
    try:
        return str(record["run_id"]), str(record["row_id"]), int(record["attempt"])
    except (KeyError, TypeError, ValueError) as exc:
        raise IntegrityError("attempt record lacks a valid run_id/row_id/attempt key") from exc


def validate_attempt_sequence(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized = [dict(record) for record in records]
    seen: dict[tuple[str, str, int], dict[str, Any]] = {}
    by_row: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in normalized:
        key = attempt_key(record)
        if key in seen:
            raise IntegrityError(f"duplicate attempt key: {key}")
        seen[key] = record
        status = str(record.get("status", ""))
        if status not in KNOWN_STATUSES:
            raise IntegrityError(f"unknown status in attempt log: {status!r}")
        max_attempts = record.get("max_attempts")
        if not isinstance(max_attempts, int) or max_attempts < 1 or key[2] > max_attempts:
            raise IntegrityError(f"attempt exceeds frozen maximum: {key}")
        by_row[key[:2]].append(record)
    for row_key, row_records in by_row.items():
        ordered = sorted(row_records, key=lambda item: int(item["attempt"]))
        attempts = [int(record["attempt"]) for record in ordered]
        if attempts != list(range(1, len(attempts) + 1)):
            raise IntegrityError(f"non-contiguous attempt sequence for {row_key}")
        max_values = {int(record["max_attempts"]) for record in ordered}
        if len(max_values) != 1:
            raise IntegrityError(f"conflicting max_attempts for {row_key}")
        prompt_digests = {str(record.get("prompt_digest", "")) for record in ordered}
        if len(prompt_digests) != 1:
            raise IntegrityError(f"conflicting prompt digests for {row_key}")
        terminal_seen = False
        for record in ordered:
            if terminal_seen:
                raise IntegrityError(f"attempt recorded after terminal state for {row_key}")
            terminal_seen = terminal_state(record, attempt_count=int(record["attempt"]))
            if bool(record.get("terminal")) != terminal_seen:
                raise IntegrityError(f"terminal flag mismatch for {row_key}")
    return normalized


def load_attempts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    data = path.read_bytes()
    if data and not data.endswith(b"\n"):
        raise IntegrityError(f"partial JSONL tail: {path.name}")
    for line_number, raw in enumerate(data.splitlines(), start=1):
        if not raw:
            raise IntegrityError(f"blank JSONL line {line_number}: {path.name}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise IntegrityError(f"corrupt JSONL line {line_number}: {path.name}") from exc
        if not isinstance(value, dict):
            raise IntegrityError(f"non-object JSONL line {line_number}: {path.name}")
        records.append(value)
    return validate_attempt_sequence(records)


def compute_attempt_count(records: Iterable[Mapping[str, Any]], run_id: str, row_id: str) -> int:
    return sum(
        1
        for record in records
        if str(record.get("run_id")) == run_id and str(record.get("row_id")) == row_id
    )


def terminal_state(record: Mapping[str, Any], *, attempt_count: int | None = None) -> bool:
    status = str(record.get("status", ""))
    if status in ALWAYS_TERMINAL_STATUSES:
        return True
    if status not in RETRYABLE_STATUSES:
        raise IntegrityError(f"unknown status: {status!r}")
    count = int(record["attempt"]) if attempt_count is None else attempt_count
    return count >= int(record["max_attempts"])


def retry_eligible(record: Mapping[str, Any], *, attempt_count: int | None = None) -> bool:
    status = str(record.get("status", ""))
    count = int(record["attempt"]) if attempt_count is None else attempt_count
    return status in RETRYABLE_STATUSES and count < int(record["max_attempts"])


def merge_shard_attempts(*groups: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    merged = [dict(record) for group in groups for record in group]
    validate_attempt_sequence(merged)
    return sorted(merged, key=lambda item: attempt_key(item))


def reconcile_attempt_snapshots(
    *groups: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Reconcile copied snapshots while rejecting conflicting attempt keys."""
    seen: dict[tuple[str, str, int], dict[str, Any]] = {}
    for group in groups:
        for source_record in group:
            record = dict(source_record)
            key = attempt_key(record)
            if key in seen and seen[key] != record:
                raise IntegrityError(f"conflicting attempt snapshots: {key}")
            seen[key] = record
    reconciled = sorted(seen.values(), key=lambda item: attempt_key(item))
    validate_attempt_sequence(reconciled)
    return reconciled


def derive_final_terminal_records(
    attempts: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    validated = validate_attempt_sequence(attempts)
    by_row: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in validated:
        by_row[(str(record["run_id"]), str(record["row_id"]))].append(record)
    finals: dict[str, dict[str, Any]] = {}
    run_ids = {key[0] for key in by_row}
    if len(run_ids) > 1:
        raise IntegrityError("attempts from multiple run IDs cannot be merged")
    for (_, row_id), row_records in by_row.items():
        last = max(row_records, key=lambda item: int(item["attempt"]))
        if terminal_state(last, attempt_count=len(row_records)):
            if row_id in finals and finals[row_id] != last:
                raise IntegrityError(f"conflicting final record: {row_id}")
            finals[row_id] = dict(last)
    return finals


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def atomic_write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    lines = [json.dumps(dict(record), ensure_ascii=False, sort_keys=True) for record in records]
    atomic_write_text(path, "\n".join(lines) + ("\n" if lines else ""))


def append_attempt(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        remaining = memoryview(payload)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("short write while appending attempt")
            remaining = remaining[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntegrityError(f"corrupted checkpoint: {path.name}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("run_id"), str):
        raise IntegrityError(f"invalid checkpoint structure: {path.name}")
    return value
