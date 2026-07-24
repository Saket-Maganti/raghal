
from __future__ import annotations
import argparse
import csv
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input_csv")
    p.add_argument("output_csv")
    p.add_argument("--results-summary")
    args = p.parse_args()
    with open(args.input_csv, newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        pending = row["pending_input"]
        if pending == "NOT_TESTED_BY_TARGETED_JUDGE":
            row["classification"] = "Conditional"
        elif args.results_summary:
            row["classification"] = "Unresolved"
        else:
            row["classification"] = "PENDING_TARGETED_JUDGE_RUN"
    fields = list(rows[0])
    with open(args.output_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

if __name__ == "__main__":
    main()
