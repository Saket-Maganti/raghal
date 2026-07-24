#!/usr/bin/env python3
"""Build a deterministic result ZIP from an explicit allow-list."""

from __future__ import annotations

import argparse
import hashlib
import json
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_zip(input_dir: Path, output_zip: Path) -> dict[str, object]:
    files = sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.name in ALLOWED_NAMES
    )
    if not files:
        raise ValueError("no allow-listed result files found")
    unknown = sorted(
        path.name
        for path in input_dir.iterdir()
        if path.is_file() and path.name not in ALLOWED_NAMES
    )
    if unknown:
        raise ValueError(f"refusing unexpected result files: {unknown}")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, path.read_bytes())
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
