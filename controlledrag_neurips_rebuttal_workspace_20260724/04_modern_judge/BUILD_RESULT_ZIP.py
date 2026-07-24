#!/usr/bin/env python3
"""Build a deterministic result ZIP from an explicit allow-list."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

ALLOWED_NAMES = {
    "run_config.json",
    "candidate_manifest.csv",
    "raw_and_parsed_outputs.jsonl",
    "attempt_log.jsonl",
    "checkpoint.json",
    "post_run_analysis.json",
    "runtime_metadata.json",
}
REQUIRED_NAMES = set(ALLOWED_NAMES)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_zip(input_dir: Path, output_zip: Path) -> dict[str, object]:
    if any(path.is_symlink() for path in input_dir.rglob("*")):
        raise ValueError("result directory must not contain symlinks")
    files = sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.name in ALLOWED_NAMES
    )
    present = {path.name for path in files}
    missing = sorted(REQUIRED_NAMES - present)
    if missing:
        raise ValueError(f"missing required result files: {missing}")
    unknown = sorted(
        path.name
        for path in input_dir.iterdir()
        if path.is_file() and path.name not in ALLOWED_NAMES
    )
    if unknown:
        raise ValueError(f"refusing unexpected result files: {unknown}")
    forbidden_names = {".env", "secrets.json", "credentials.json"}
    nested_forbidden = [
        path.relative_to(input_dir).as_posix()
        for path in input_dir.rglob("*")
        if path.is_file()
        and (
            path.name in forbidden_names
            or "__pycache__" in path.parts
            or "cache" in path.name.lower()
        )
    ]
    if nested_forbidden:
        raise ValueError(f"forbidden files present in result tree: {nested_forbidden}")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_zip.name}.", dir=output_zip.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for path in files:
                info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o600 << 16
                archive.writestr(info, path.read_bytes())
        os.replace(temporary, output_zip)
    finally:
        if temporary.exists():
            temporary.unlink()
    receipt = {
        "zip": output_zip.name,
        "zip_sha256": sha256_file(output_zip),
        "files": [
            {"name": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in files
        ],
    }
    print(json.dumps(receipt, indent=2))
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-zip", type=Path, required=True)
    args = parser.parse_args()
    build_zip(args.input_dir, args.output_zip)


if __name__ == "__main__":
    main()
