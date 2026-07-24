
"""Merge immutable per-rank shards without dropping malformed outputs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def merge(output_root: str | Path) -> dict:
    root = Path(output_root)
    records = []
    for rank in (0, 1):
        path = root / "raw_outputs" / f"gpu{rank}.jsonl"
        if not path.exists():
            raise FileNotFoundError(path)
        records.extend(json.loads(line) for line in path.read_text().splitlines() if line)
    keys = [(r["experiment_row_id"], r["interface"]) for r in records]
    duplicates = len(keys) - len(set(keys))
    merged = sorted(records, key=lambda r: (r["experiment_row_id"], r["interface"]))
    path = root / "raw_outputs/merged_outputs.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in merged),
        encoding="utf-8",
    )
    return {"records": len(merged), "duplicates": duplicates, "path": str(path)}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root")
    args = parser.parse_args()
    print(json.dumps(merge(args.output_root), indent=2))

if __name__ == "__main__":
    main()
