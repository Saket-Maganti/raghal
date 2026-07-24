
"""Deterministic hashing helpers."""
from __future__ import annotations
import hashlib
import json
import re
import unicodedata
from pathlib import Path

def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).strip()).casefold()

def semantic_digest(row: dict) -> str:
    fields = [normalize_text(str(row[k])) for k in ("question", "retrieved_context", "answer")]
    fields.append(str(row["system"]))
    return hashlib.sha256("\x1f".join(fields).encode()).hexdigest()

def deterministic_shard(experiment_row_id: str, interface: str, world_size: int = 2) -> int:
    payload = f"{experiment_row_id}{interface}".encode()
    return int(hashlib.sha256(payload).hexdigest(), 16) % world_size
