
"""Render bounded rebuttal tables only from validated analysis CSVs."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path

def rows(path: Path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))

def table(data: list[dict], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    lines += ["| " + " | ".join(str(row.get(c, "")) for c in columns) + " |" for row in data]
    return "\n".join(lines) + "\n"

def build(output_root: str | Path) -> None:
    root = Path(output_root)
    analysis, out = root / "analysis", root / "tables"
    out.mkdir(parents=True, exist_ok=True)
    (out / "REBUTTAL_TABLE_MODERN_JUDGE.md").write_text(
        "# Modern judge fixed-output contrast\n\n" + table(
            rows(analysis / "MAIN_SYSTEM_CONTRASTS.csv"),
            ["interface", "n_pairs", "baseline_mean", "hcpc_v1_mean", "baseline_minus_hcpc_v1", "ci_low", "ci_high"],
        )
    )
    calibration = rows(analysis / "HUMAN_TYPICAL_CALIBRATION.csv") + rows(
        analysis / "HUMAN_DISAGREEMENT_CALIBRATION.csv"
    )
    (out / "REBUTTAL_TABLE_HUMAN_CALIBRATION.md").write_text(
        "# Same-row human calibration\n\n" + table(
            calibration, ["panel", "interface", "n", "spearman", "average_precision_faithful_1", "valid_output_rate"]
        )
    )
    claim = analysis / "CLAIM_STABILITY_TABLE.csv"
    (out / "REBUTTAL_TABLE_CLAIM_STABILITY.md").write_text(
        "# Claim stability\n\n" + (claim.read_text() if claim.exists() else "PENDING_CLAIM_STABILITY_BUILD\n")
    )
    (out / "REBUTTAL_RESULTS_PLAIN_TEXT.md").write_text(
        "# Bounded results handoff\n\nUse only after validity-gate review and professor approval.\n"
    )

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root")
    args = parser.parse_args()
    build(args.output_root)

if __name__ == "__main__":
    main()
