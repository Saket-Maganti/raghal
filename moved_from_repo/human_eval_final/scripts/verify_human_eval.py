#!/usr/bin/env python3
"""Verify completed Fix 3 human-evaluation statistics.

This script is intentionally local-only: it reads completed annotation files,
computes agreement and metric correlations, and writes the CSV artifacts used
by the paper plus a compact verification summary.
"""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIX_DIR = ROOT / "data/revision/fix_03"
RESULT_DIR = ROOT / "results/revision/fix_03"
TEMPLATE = FIX_DIR / "human_eval_template.jsonl"
RATER_A = FIX_DIR / "human_eval_rater_a.csv"
RATER_B = FIX_DIR / "human_eval_rater_b.csv"
ADJUDICATED = FIX_DIR / "human_eval_adjudicated.csv"
SUMMARY_OUT = RESULT_DIR / "human_eval_summary.csv"
LABEL_DIST_OUT = RESULT_DIR / "human_eval_label_distribution.csv"
CORR_OUT = RESULT_DIR / "human_eval_correlations.csv"
BOOTSTRAP_OUT = RESULT_DIR / "bootstrap_correlation_cis.csv"
OUT = RESULT_DIR / "human_eval_verification.csv"
OUT_MD = RESULT_DIR / "human_eval_verification.md"

LABEL_VALUES = {
    "unsupported": 0.0,
    "partially_supported": 0.5,
    "supported": 1.0,
}
METRICS = ["auto_deberta", "auto_second_nli", "auto_ragas"]
METRIC_NAMES = {
    "auto_deberta": "DeBERTa-v3 NLI",
    "auto_second_nli": "Second NLI",
    "auto_ragas": "RAGAS-style judge",
}


def normalize(label: str) -> str:
    return label.strip().lower().replace("-", "_").replace(" ", "_")


def load_jsonl_by_id(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            rows[str(row["id"])] = row
    return rows


def load_csv_by_id(path: Path) -> dict[str, dict]:
    with path.open(newline="") as handle:
        return {str(row["id"]): row for row in csv.DictReader(handle)}


def require_label(value: str, row_id: str, column: str) -> str:
    label = normalize(value)
    if label not in LABEL_VALUES:
        raise ValueError(f"Row {row_id} invalid {column}={value!r}")
    return label


def pearson(xs: list[float], ys: list[float]) -> float:
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    return float("nan") if den_x == 0 or den_y == 0 else num / (den_x * den_y)


def average_ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = rank
        i = j
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float:
    return pearson(average_ranks(xs), average_ranks(ys))


def kendall_tau_b(xs: list[float], ys: list[float]) -> float:
    concordant = 0
    discordant = 0
    ties_x = 0
    ties_y = 0
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            dx = (xs[i] > xs[j]) - (xs[i] < xs[j])
            dy = (ys[i] > ys[j]) - (ys[i] < ys[j])
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                ties_x += 1
            elif dy == 0:
                ties_y += 1
            elif dx == dy:
                concordant += 1
            else:
                discordant += 1
    denominator = math.sqrt((concordant + discordant + ties_x) * (concordant + discordant + ties_y))
    return float("nan") if denominator == 0 else (concordant - discordant) / denominator


def cohen_kappa(labels_a: list[str], labels_b: list[str]) -> float:
    if len(labels_a) != len(labels_b):
        raise ValueError("Rater vectors differ in length")
    n = len(labels_a)
    observed = sum(a == b for a, b in zip(labels_a, labels_b)) / n
    counts_a = Counter(labels_a)
    counts_b = Counter(labels_b)
    expected = sum((counts_a[label] / n) * (counts_b[label] / n) for label in LABEL_VALUES)
    return 1.0 if math.isclose(expected, 1.0) else (observed - expected) / (1.0 - expected)


def bootstrap_bounds(
    xs: list[float],
    ys: list[float],
    fn,
    n_bootstrap: int = 10000,
    seed: int = 20260429,
) -> tuple[float, float]:
    rng = random.Random(seed)
    values: list[float] = []
    n = len(xs)
    for _ in range(n_bootstrap):
        sample_idx = [rng.randrange(n) for _ in range(n)]
        sample_x = [xs[i] for i in sample_idx]
        sample_y = [ys[i] for i in sample_idx]
        values.append(fn(sample_x, sample_y))
    values.sort()
    low_idx = int(0.025 * n_bootstrap)
    high_idx = int(0.975 * n_bootstrap)
    return values[low_idx], values[high_idx]


def main() -> None:
    template = load_jsonl_by_id(TEMPLATE)
    rater_a = load_csv_by_id(RATER_A)
    rater_b = load_csv_by_id(RATER_B)
    adjudicated = load_csv_by_id(ADJUDICATED)
    ids = sorted(template, key=lambda value: int(value) if value.isdigit() else value)

    missing = (set(ids) - set(rater_a)) | (set(ids) - set(rater_b)) | (set(ids) - set(adjudicated))
    if missing:
        raise ValueError(f"Missing annotation ids: {sorted(missing)[:10]}")

    labels_a = [require_label(rater_a[row_id]["label"], row_id, "rater_a.label") for row_id in ids]
    labels_b = [require_label(rater_b[row_id]["label"], row_id, "rater_b.label") for row_id in ids]
    final_labels = [
        require_label(adjudicated[row_id]["adjudicated_label"], row_id, "adjudicated.adjudicated_label")
        for row_id in ids
    ]
    final_scores = [LABEL_VALUES[label] for label in final_labels]

    raw_agreement = sum(a == b for a, b in zip(labels_a, labels_b)) / len(ids)
    exact_matches = sum(a == b for a, b in zip(labels_a, labels_b))
    kappa = cohen_kappa(labels_a, labels_b)
    distribution = Counter(final_labels)

    correlation_rows: list[dict[str, str]] = []
    bootstrap_rows: list[dict[str, str]] = []
    for metric in METRICS:
        metric_scores = [float(template[row_id][metric]) for row_id in ids]
        spearman_est = spearman(final_scores, metric_scores)
        pearson_est = pearson(final_scores, metric_scores)
        kendall_est = kendall_tau_b(final_scores, metric_scores)
        correlation_rows.append(
            {
                "metric": metric,
                "metric_name": METRIC_NAMES[metric],
                "spearman_rho": f"{spearman_est:.6f}",
                "pearson_r": f"{pearson_est:.6f}",
                "kendall_tau_b": f"{kendall_est:.6f}",
                "n": str(len(ids)),
            }
        )
        pearson_low, pearson_high = bootstrap_bounds(final_scores, metric_scores, pearson)
        spearman_low, spearman_high = bootstrap_bounds(final_scores, metric_scores, spearman)
        bootstrap_rows.extend(
            [
                {
                    "table": "6_human_calibration",
                    "item": METRIC_NAMES[metric],
                    "n": str(len(ids)),
                    "statistic": "pearson_r",
                    "estimate": f"{pearson_est:.6f}",
                    "ci_low": f"{pearson_low:.6f}",
                    "ci_high": f"{pearson_high:.6f}",
                    "n_bootstrap": "10000",
                    "seed": "20260429",
                    "ci_method": "paired percentile bootstrap",
                },
                {
                    "table": "6_human_calibration",
                    "item": METRIC_NAMES[metric],
                    "n": str(len(ids)),
                    "statistic": "spearman_rho",
                    "estimate": f"{spearman_est:.6f}",
                    "ci_low": f"{spearman_low:.6f}",
                    "ci_high": f"{spearman_high:.6f}",
                    "n_bootstrap": "10000",
                    "seed": "20260429",
                    "ci_method": "paired percentile bootstrap",
                },
            ]
        )

    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    with SUMMARY_OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "n_examples",
                "n_raters",
                "label_scheme",
                "raw_agreement",
                "cohen_kappa",
                "final_label_source",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "n_examples": len(ids),
                "n_raters": 2,
                "label_scheme": "supported / partially_supported / unsupported",
                "raw_agreement": f"{raw_agreement:.6f}",
                "cohen_kappa": f"{kappa:.6f}",
                "final_label_source": "adjudicated_label",
            }
        )

    with LABEL_DIST_OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["label", "count", "proportion"])
        writer.writeheader()
        for label in ["unsupported", "partially_supported", "supported"]:
            writer.writerow(
                {
                    "label": label,
                    "count": distribution[label],
                    "proportion": f"{distribution[label] / len(ids):.6f}",
                }
            )

    with CORR_OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["metric", "metric_name", "spearman_rho", "pearson_r", "kendall_tau_b", "n"],
        )
        writer.writeheader()
        writer.writerows(correlation_rows)

    existing_bootstrap_rows: list[dict[str, str]] = []
    if BOOTSTRAP_OUT.exists():
        with BOOTSTRAP_OUT.open(newline="") as handle:
            existing_bootstrap_rows = list(csv.DictReader(handle))
    existing_bootstrap_rows = [row for row in existing_bootstrap_rows if row.get("table") != "6_human_calibration"]
    existing_bootstrap_rows.extend(bootstrap_rows)
    with BOOTSTRAP_OUT.open("w", newline="") as handle:
        fieldnames = [
            "table",
            "item",
            "n",
            "statistic",
            "estimate",
            "ci_low",
            "ci_high",
            "n_bootstrap",
            "seed",
            "ci_method",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_bootstrap_rows)

    verification_rows: list[dict[str, str]] = [
        {
            "statistic": "summary",
            "n_examples": str(len(ids)),
            "n_raters": "2",
            "raw_agreement": f"{raw_agreement:.6f}",
            "cohen_kappa": f"{kappa:.6f}",
            "unsupported": str(distribution["unsupported"]),
            "partially_supported": str(distribution["partially_supported"]),
            "supported": str(distribution["supported"]),
            "metric": "",
            "spearman_rho": "",
            "pearson_r": "",
            "kendall_tau_b": "",
        }
    ]
    for row in correlation_rows:
        verification_rows.append(
            {
                "statistic": "metric_correlation",
                "n_examples": str(len(ids)),
                "n_raters": "2",
                "raw_agreement": "",
                "cohen_kappa": "",
                "unsupported": "",
                "partially_supported": "",
                "supported": "",
                "metric": row["metric"],
                "spearman_rho": row["spearman_rho"],
                "pearson_r": row["pearson_r"],
                "kendall_tau_b": row["kendall_tau_b"],
            }
        )

    with OUT.open("w", newline="") as handle:
        fieldnames = [
            "statistic",
            "n_examples",
            "n_raters",
            "raw_agreement",
            "cohen_kappa",
            "unsupported",
            "partially_supported",
            "supported",
            "metric",
            "spearman_rho",
            "pearson_r",
            "kendall_tau_b",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(verification_rows)

    md_lines = [
        "# Human Evaluation Verification",
        "",
        "Computed from `data/revision/fix_03/human_eval_rater_a.csv`, "
        "`data/revision/fix_03/human_eval_rater_b.csv`, "
        "`data/revision/fix_03/human_eval_adjudicated.csv`, and "
        "`data/revision/fix_03/human_eval_template.jsonl`.",
        "",
        f"- n: {len(ids)}",
        "- raters: 2",
        f"- raw agreement: {raw_agreement:.6f} ({exact_matches} of {len(ids)} exact-match)",
        f"- Cohen's kappa: {kappa:.6f}",
        (
            "- adjudicated labels: "
            f"{distribution['supported']} supported, "
            f"{distribution['partially_supported']} partially supported, "
            f"{distribution['unsupported']} unsupported"
        ),
        "",
        "| Metric | Spearman rho | Pearson r | Kendall tau-b |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in correlation_rows:
        md_lines.append(
            f"| {row['metric_name']} | {row['spearman_rho']} | "
            f"{row['pearson_r']} | {row['kendall_tau_b']} |"
        )
    md_lines.extend(
        [
            "",
            "Status: recomputed from the adjudicated file after case-by-case disagreement review.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(md_lines))

    for row in verification_rows:
        print(row)


if __name__ == "__main__":
    main()
