
"""Verify private input checksums, schemas, counts, and frozen identities."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from judge_schema import parse_judge_output
from render_prompts import normalized_symmetry
from utils_hashing import semantic_digest, sha256_file

def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

def verify_checksums(root: Path) -> tuple[bool, list[str]]:
    mismatches = []
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = root / relative
        if not path.is_file() or sha256_file(path) != expected:
            mismatches.append(relative)
    return not mismatches, mismatches

def validate_bundle(root: str | Path) -> dict:
    root = Path(root)
    checksum_ok, mismatches = verify_checksums(root)
    summary = json.loads((root / "manifests/MANIFEST_SUMMARY.json").read_text())
    lock = json.loads((root / "MODEL_LOCK.json").read_text())
    rows = read_jsonl(root / "manifests/all_frozen_rows.jsonl")
    ids = [r["experiment_row_id"] for r in rows]
    semantics = [semantic_digest(r) for r in rows]
    required = {
        "experiment_row_id", "source_row_id", "panel", "system", "dataset", "split",
        "question", "retrieved_context", "answer", "human_label",
        "human_label_available", "human_slice", "pair_id", "output_origin",
        "provenance_source", "provenance_sha256"
    }
    schema_ok = all(set(row) == required for row in rows)
    counts_ok = (
        len(rows) == summary["all_frozen_rows"]
        and sum(r["panel"] == "main_600" for r in rows) == summary["main_eligible"]
        and sum(r["panel"] == "human_typical" for r in rows) == summary["typical_eligible"]
        and sum(r["panel"] == "human_disagreement" for r in rows)
        == summary["disagreement_eligible"]
    )
    result = {
        "checksum_ok": checksum_ok,
        "checksum_mismatches": mismatches,
        "schema_ok": schema_ok,
        "counts_ok": counts_ok,
        "unique_ids": len(ids) == len(set(ids)),
        "unique_semantics": len(semantics) == len(set(semantics)),
        "model_lock_ok": (
            lock["model_id"] == "Qwen/Qwen2.5-7B-Instruct"
            and lock["revision"] == "a09a35458c702b33eeacc393d103063234e8bc28"
            and lock["quantization"] == "bitsandbytes_nf4_4bit"
        ),
        "prompt_symmetry_ok": normalized_symmetry(root),
        "model_loaded": False,
        "network_inference_calls": 0,
        "real_rows_scored": 0,
    }
    result["ok"] = all(
        result[key]
        for key in (
            "checksum_ok", "schema_ok", "counts_ok", "unique_ids",
            "unique_semantics", "model_lock_ok", "prompt_symmetry_ok"
        )
    )
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_root")
    args = parser.parse_args()
    result = validate_bundle(args.bundle_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 2)

if __name__ == "__main__":
    main()
