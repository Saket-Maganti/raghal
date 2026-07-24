#!/usr/bin/env python3
"""Verify the final n=99 human-evaluation calibration files."""

from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = ROOT / "human_eval_final" / "n99_calibration"
RESULT_DIR = ROOT / "results" / "revision" / "fix_03"

ADJUDICATED = FINAL_DIR / "human_eval_adjudicated.csv"
SUMMARY = FINAL_DIR / "human_eval_summary.csv"
LABEL_DIST = FINAL_DIR / "human_eval_label_distribution.csv"
CORRELATIONS = FINAL_DIR / "human_eval_correlations.csv"
OUT = RESULT_DIR / "human_eval_verification.csv"

LABELS = ["unsupported", "partially_supported", "supported"]


def normalize(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def cohen_kappa(labels_a: list[str], labels_b: list[str]) -> float:
    if len(labels_a) != len(labels_b):
        raise ValueError("Rater vectors differ in length")
    n = len(labels_a)
    observed = sum(a == b for a, b in zip(labels_a, labels_b)) / n
    counts_a = Counter(labels_a)
    counts_b = Counter(labels_b)
    expected = sum((counts_a[label] / n) * (counts_b[label] / n) for label in LABELS)
    return 1.0 if math.isclose(expected, 1.0) else (observed - expected) / (1.0 - expected)


def require_close(name: str, observed: float, expected: float, tolerance: float = 5e-4) -> None:
    if not math.isclose(observed, expected, abs_tol=tolerance):
        raise AssertionError(f"{name}: observed {observed:.6f}, expected {expected:.6f}")


def main() -> None:
    adjudicated = read_rows(ADJUDICATED)
    labels_a = [normalize(row["rater_a_label"]) for row in adjudicated]
    labels_b = [normalize(row["rater_b_label"]) for row in adjudicated]
    final_labels = [normalize(row["adjudicated_label"]) for row in adjudicated]

    if any(label not in LABELS for label in labels_a + labels_b + final_labels):
        raise ValueError("Unexpected label in final human-evaluation file")

    n = len(adjudicated)
    raw_agreement = sum(a == b for a, b in zip(labels_a, labels_b)) / n
    kappa = cohen_kappa(labels_a, labels_b)
    distribution = Counter(final_labels)

    summary = read_rows(SUMMARY)[0]
    require_close("raw agreement", raw_agreement, float(summary["raw_agreement"]))
    require_close("Cohen's kappa", kappa, float(summary["cohen_kappa"]))

    label_dist_rows = {row["label"]: int(row["count"]) for row in read_rows(LABEL_DIST)}
    for label in LABELS:
        if distribution[label] != label_dist_rows[label]:
            raise AssertionError(
                f"{label}: observed {distribution[label]}, expected {label_dist_rows[label]}"
            )

    correlation_rows = read_rows(CORRELATIONS)
    spearmans = [float(row["spearman_rho"]) for row in correlation_rows]

    require_close("n", float(n), 99.0, tolerance=0.0)
    require_close("raw agreement expected", raw_agreement, 0.919192)
    require_close("Cohen's kappa expected", kappa, 0.773779)
    if [distribution["supported"], distribution["partially_supported"], distribution["unsupported"]] != [79, 16, 4]:
        raise AssertionError("Unexpected adjudicated label distribution")
    for name, observed, expected in zip(
        ["DeBERTa Spearman", "second NLI Spearman", "RAGAS-style Spearman"],
        spearmans,
        [0.103023, 0.393969, 0.548699],
    ):
        require_close(name, observed, expected)

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as handle:
        fieldnames = [
            "statistic",
            "n_examples",
            "raw_agreement",
            "cohen_kappa",
            "supported",
            "partially_supported",
            "unsupported",
            "spearman_deberta",
            "spearman_second_nli",
            "spearman_ragas_style",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "statistic": "n99_human_eval",
                "n_examples": n,
                "raw_agreement": f"{raw_agreement:.6f}",
                "cohen_kappa": f"{kappa:.6f}",
                "supported": distribution["supported"],
                "partially_supported": distribution["partially_supported"],
                "unsupported": distribution["unsupported"],
                "spearman_deberta": f"{spearmans[0]:.6f}",
                "spearman_second_nli": f"{spearmans[1]:.6f}",
                "spearman_ragas_style": f"{spearmans[2]:.6f}",
            }
        )

    print("n=99 typical-row calibration verified")
    print(f"raw agreement: {raw_agreement:.3f}")
    print(f"Cohen's kappa: {kappa:.3f}")
    print(
        "adjudicated distribution: "
        f"{distribution['supported']}/{distribution['partially_supported']}/{distribution['unsupported']}"
    )
    print("Spearman correlations: " + "/".join(f"{value:.3f}" for value in spearmans))


if __name__ == "__main__":
    main()
