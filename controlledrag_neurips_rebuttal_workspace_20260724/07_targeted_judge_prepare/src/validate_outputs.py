
"""Validate complete output coverage and preserve every failure category."""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from judge_schema import parse_judge_output

def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]

def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def validate(bundle_root: str | Path, output_root: str | Path) -> dict:
    bundle, output = Path(bundle_root), Path(output_root)
    expected_rows = load_jsonl(bundle / "manifests/all_frozen_rows.jsonl")
    expected = {(r["experiment_row_id"], i) for r in expected_rows for i in ("answer_only", "context_conditioned")}
    records = load_jsonl(output / "raw_outputs/merged_outputs.jsonl")
    counts = Counter((r["experiment_row_id"], r["interface"]) for r in records)
    duplicates = sorted(k for k, n in counts.items() if n > 1)
    actual = set(counts)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    invalid = []
    categories = Counter()
    for record in records:
        parsed, error = parse_judge_output(record.get("raw_output", ""))
        if (
            record.get("model_id") != "Qwen/Qwen2.5-7B-Instruct"
            or record.get("model_revision") != "a09a35458c702b33eeacc393d103063234e8bc28"
        ):
            error = "wrong_model_identity"
            parsed = None
        if parsed is None:
            categories[error] += 1
            invalid.append({**record, "validation_error": error})
    validation = output / "validation"
    validation.mkdir(parents=True, exist_ok=True)
    (validation / "INVALID_OUTPUTS.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in invalid)
    )
    write_csv(
        validation / "MISSING_OUTPUTS.csv",
        [{"experiment_row_id": a, "interface": b} for a, b in missing],
        ["experiment_row_id", "interface"],
    )
    write_csv(
        validation / "DUPLICATE_OUTPUTS.csv",
        [{"experiment_row_id": a, "interface": b, "count": counts[(a, b)]} for a, b in duplicates],
        ["experiment_row_id", "interface", "count"],
    )
    row_lookup = {r["experiment_row_id"]: r for r in expected_rows}
    requested = defaultdict(int)
    valid = defaultdict(int)
    for row_id, interface in expected:
        key = (row_lookup[row_id]["system"], interface)
        requested[key] += 1
        matching = [r for r in records if (r["experiment_row_id"], r["interface"]) == (row_id, interface)]
        if len(matching) == 1 and parse_judge_output(matching[0].get("raw_output", ""))[0] is not None:
            valid[key] += 1
    diff_rows = []
    for key in sorted(requested):
        rate = valid[key] / requested[key] if requested[key] else 0.0
        diff_rows.append(
            {"system": key[0], "interface": key[1], "requested": requested[key], "valid": valid[key], "valid_rate": rate}
        )
    write_csv(
        validation / "DIFFERENTIAL_MISSINGNESS.csv",
        diff_rows, ["system", "interface", "requested", "valid", "valid_rate"]
    )
    result = {
        "requested_outputs": len(expected),
        "received_records": len(records),
        "valid_records": len(records) - len(invalid),
        "invalid_records": len(invalid),
        "invalid_categories": dict(categories),
        "missing_outputs": len(missing),
        "duplicate_keys": len(duplicates),
        "unexpected_outputs": len(unexpected),
        "valid_output_rate": (len(records) - len(invalid)) / len(expected),
        "ok": not invalid and not missing and not duplicates and not unexpected and len(records) == len(expected),
    }
    (validation / "OUTPUT_VALIDATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_root")
    parser.add_argument("output_root")
    args = parser.parse_args()
    result = validate(args.bundle_root, args.output_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 2)

if __name__ == "__main__":
    main()
