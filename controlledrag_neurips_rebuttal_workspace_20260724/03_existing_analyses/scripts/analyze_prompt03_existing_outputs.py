#!/usr/bin/env python3
"""Verify human panels and analyze fixed, already-produced outputs for Prompt 03.

This script performs no retrieval, generation, model loading, or network access.
It reads the immutable submitted artifact and the provenance-approved recovered
tree, then writes compact derived CSV/JSON results into the rebuttal workspace.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import warnings
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import scipy
from scipy.stats import kendalltau, pearsonr, spearmanr
import sklearn
from sklearn.metrics import (
    average_precision_score,
    cohen_kappa_score,
    roc_auc_score,
)


SEED = 20260724
N_BOOTSTRAP = 10_000
SCORER_DISPLAY = {
    "auto_deberta": "legacy_deberta_proxy",
    "auto_second_nli": "legacy_second_nli_proxy",
    "auto_ragas": "ragas_style_judge",
    "deberta_score": "legacy_deberta_proxy",
    "second_nli_score": "legacy_second_nli_proxy",
    "ragas_style_score": "ragas_style_judge",
}

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[3]
PROJECT_ROOT = REPO_ROOT.parents[1]
WORKSPACE = REPO_ROOT / "controlledrag_neurips_rebuttal_workspace_20260724"
HUMAN_OUT = WORKSPACE / "02_human_eval"
ANALYSIS_OUT = WORKSPACE / "03_existing_analyses"
RESULTS_OUT = ANALYSIS_OUT / "results"

SUBMITTED = PROJECT_ROOT / "rag-hallucination-detection_main"
RECOVERED = (
    PROJECT_ROOT
    / "cleanup_20260506_final_code_artifact_cleanup"
    / "root_before_cleanup"
)

INPUTS = {
    "n99_adjudicated": SUBMITTED
    / "human_eval_final/n99_calibration/human_eval_adjudicated.csv",
    "n99_submitted_correlations": SUBMITTED
    / "human_eval_final/n99_calibration/human_eval_correlations.csv",
    "n99_submitted_bootstrap": SUBMITTED
    / "human_eval_final/n99_calibration/bootstrap_correlation_cis.csv",
    "n99_recovered_scores": RECOVERED
    / "data/revision/fix_03/human_eval_template.jsonl",
    "n100_adjudicated": SUBMITTED
    / "human_eval_final/n100_disagreement/annotation_batch_disagreement_100.csv",
    "n100_submitted_correlations": SUBMITTED
    / "human_eval_final/n100_disagreement/human_disagreement_correlations.csv",
    "n100_submitted_binary": SUBMITTED
    / "human_eval_final/n100_disagreement/human_disagreement_auroc_auprc.csv",
    "n100_submitted_bootstrap": SUBMITTED
    / "human_eval_final/n100_disagreement/human_disagreement_bootstrap_cis.csv",
    "context_n600": RECOVERED
    / "results/revision/context_conditioned_nli/per_query_n600.csv",
    "context_n99_summary": RECOVERED
    / "results/revision/context_conditioned_nli/n99_alignment_summary.csv",
    "threshold_tau_summary": RECOVERED
    / "results/revision/fix_04/tau_summary.csv",
    "threshold_transfer_matrix": RECOVERED
    / "results/revision/fix_04/tau_transfer_matrix.csv",
    "pareto_summary": RECOVERED
    / "results/revision/fix_06/h2h_summary_with_ci.csv",
    "pareto_per_query": RECOVERED
    / "data/revision/fix_06/per_query_compact.csv",
}


def project_relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix == ".jsonl":
        return pd.read_json(path, lines=True)
    return pd.read_csv(path)


def percentile_ci(values: list[float]) -> tuple[float, float, int]:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=float)
    if finite.size == 0:
        return np.nan, np.nan, 0
    lower, upper = np.quantile(finite, [0.025, 0.975])
    return float(lower), float(upper), int(finite.size)


def safe_corr(x: np.ndarray, y: np.ndarray, kind: str) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    x_valid = x[mask]
    y_valid = y[mask]
    if x_valid.size < 3 or np.unique(x_valid).size < 2 or np.unique(y_valid).size < 2:
        return np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if kind == "pearson":
            return float(pearsonr(x_valid, y_valid).statistic)
        if kind == "spearman":
            return float(spearmanr(x_valid, y_valid).statistic)
        if kind == "kendall":
            return float(kendalltau(x_valid, y_valid).statistic)
    raise ValueError(f"Unknown correlation kind: {kind}")


def safe_auc(y: np.ndarray, scores: np.ndarray, metric: str) -> float:
    mask = np.isfinite(y) & np.isfinite(scores)
    y_valid = y[mask].astype(int)
    score_valid = scores[mask].astype(float)
    if y_valid.size == 0 or np.unique(y_valid).size != 2:
        return np.nan
    if metric == "auroc":
        return float(roc_auc_score(y_valid, score_valid))
    if metric == "average_precision":
        return float(average_precision_score(y_valid, score_valid))
    raise ValueError(f"Unknown binary metric: {metric}")


def bootstrap_single(
    arrays: list[np.ndarray],
    statistic: Callable[..., float],
    *,
    seed: int,
    n_bootstrap: int = N_BOOTSTRAP,
) -> tuple[float, float, int]:
    n_rows = len(arrays[0])
    if any(len(array) != n_rows for array in arrays):
        raise ValueError("Bootstrap arrays must have equal length.")
    rng = np.random.default_rng(seed)
    values: list[float] = []
    for _ in range(n_bootstrap):
        indices = rng.integers(0, n_rows, size=n_rows)
        value = statistic(*(array[indices] for array in arrays))
        if np.isfinite(value):
            values.append(float(value))
    return percentile_ci(values)


def assert_close(actual: float, expected: float, label: str, atol: float = 5e-7) -> None:
    if not np.isclose(actual, expected, atol=atol, rtol=0):
        raise AssertionError(f"{label}: recomputed={actual}, submitted={expected}")


def verify_inputs() -> pd.DataFrame:
    rows = []
    for name, path in INPUTS.items():
        if not path.is_file():
            raise FileNotFoundError(f"Required input missing: {project_relative(path)}")
        rows.append(
            {
                "input_id": name,
                "project_relative_path": project_relative(path),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
                "access": "read_only",
                "provenance_status": "provenance_safe_fixed_output",
            }
        )
    return pd.DataFrame(rows)


def verify_human_panels() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    n99 = read_table(INPUTS["n99_adjudicated"])
    n99_scores = read_table(INPUTS["n99_recovered_scores"])
    n100 = read_table(INPUTS["n100_adjudicated"])

    if len(n99) != 99 or len(n100) != 100:
        raise AssertionError("Human panel row counts do not match n=99 and n=100.")
    if not n99["id"].is_unique:
        raise AssertionError("n=99 IDs are not unique.")
    if not n100["example_id"].is_unique or not n100["query_id"].is_unique:
        raise AssertionError("n=100 example_id/query_id fields are not unique.")
    if set(n99["id"]) != set(n99_scores["id"]):
        raise AssertionError("n=99 adjudication and scorer IDs do not match exactly.")

    n99_essential = [
        "id",
        "dataset",
        "condition",
        "rater_a_label",
        "rater_b_label",
        "adjudicated_label",
    ]
    n100_essential = [
        "example_id",
        "query_id",
        "dataset",
        "condition",
        "human_label_rater1",
        "human_label_rater2",
        "adjudicated_label",
        "deberta_score",
        "second_nli_score",
        "ragas_style_score",
    ]
    if int(n99[n99_essential].isna().sum().sum()) != 0:
        raise AssertionError("n=99 has missing load-bearing fields.")
    if int(n100[n100_essential].isna().sum().sum()) != 0:
        raise AssertionError("n=100 has missing load-bearing fields.")

    diagnostics = []
    for panel, frame, id_col, essential in [
        ("n99_typical", n99, "id", n99_essential),
        ("n100_disagreement_targeted", n100, "example_id", n100_essential),
    ]:
        diagnostics.append(
            {
                "panel": panel,
                "n_rows": len(frame),
                "id_column": id_col,
                "unique_ids": frame[id_col].nunique(),
                "duplicate_ids": int(frame[id_col].duplicated().sum()),
                "missing_essential_cells": int(frame[essential].isna().sum().sum()),
                "conditions": ";".join(
                    f"{key}:{value}"
                    for key, value in frame["condition"].value_counts().sort_index().items()
                ),
                "status": "verified_complete",
            }
        )

    label_rows = []
    label_specs = [
        (
            "n99_typical",
            n99,
            ["rater_a_label", "rater_b_label", "adjudicated_label"],
        ),
        (
            "n100_disagreement_targeted",
            n100,
            ["human_label_rater1", "human_label_rater2", "adjudicated_label"],
        ),
    ]
    for panel, frame, columns in label_specs:
        for column in columns:
            for label, count in frame[column].value_counts(dropna=False).sort_index().items():
                label_rows.append(
                    {
                        "panel": panel,
                        "label_source": column,
                        "label": str(label),
                        "count": int(count),
                        "proportion": float(count / len(frame)),
                    }
                )

    agreement_rows = []
    for panel, frame, a_col, b_col in [
        ("n99_typical", n99, "rater_a_label", "rater_b_label"),
        (
            "n100_disagreement_targeted",
            n100,
            "human_label_rater1",
            "human_label_rater2",
        ),
    ]:
        a = frame[a_col].astype(str).to_numpy()
        b = frame[b_col].astype(str).to_numpy()
        agreement = float(np.mean(a == b))
        kappa = float(cohen_kappa_score(a, b))
        disagreements = int(np.sum(a != b))
        for offset, metric, estimate, fn in [
            (1, "raw_agreement", agreement, lambda x, y: float(np.mean(x == y))),
            (
                2,
                "unweighted_cohen_kappa",
                kappa,
                lambda x, y: float(cohen_kappa_score(x, y)),
            ),
        ]:
            lower, upper, valid = bootstrap_single(
                [a, b], fn, seed=SEED + offset + len(frame)
            )
            agreement_rows.append(
                {
                    "panel": panel,
                    "metric": metric,
                    "estimate": estimate,
                    "ci_lower": lower,
                    "ci_upper": upper,
                    "n": len(frame),
                    "valid_bootstrap_samples": valid,
                    "n_bootstrap": N_BOOTSTRAP,
                    "seed": SEED + offset + len(frame),
                    "label_timing": "pre_adjudication",
                }
            )
        agreement_rows.append(
            {
                "panel": panel,
                "metric": "disagreement_count",
                "estimate": disagreements,
                "ci_lower": np.nan,
                "ci_upper": np.nan,
                "n": len(frame),
                "valid_bootstrap_samples": np.nan,
                "n_bootstrap": np.nan,
                "seed": np.nan,
                "label_timing": "pre_adjudication",
            }
        )

    agreement_df = pd.DataFrame(agreement_rows)
    assert_close(
        agreement_df.query(
            "panel == 'n99_typical' and metric == 'raw_agreement'"
        )["estimate"].iloc[0],
        0.9191919191919192,
        "n99 raw agreement",
    )
    assert_close(
        agreement_df.query(
            "panel == 'n99_typical' and metric == 'unweighted_cohen_kappa'"
        )["estimate"].iloc[0],
        0.773779163242075,
        "n99 kappa",
    )
    assert_close(
        agreement_df.query(
            "panel == 'n100_disagreement_targeted' and metric == 'raw_agreement'"
        )["estimate"].iloc[0],
        0.88,
        "n100 raw agreement",
    )
    assert_close(
        agreement_df.query(
            "panel == 'n100_disagreement_targeted' and metric == 'unweighted_cohen_kappa'"
        )["estimate"].iloc[0],
        0.7209302325581396,
        "n100 kappa",
    )

    return pd.DataFrame(diagnostics), pd.DataFrame(label_rows), agreement_df


def verify_human_metrics() -> tuple[pd.DataFrame, pd.DataFrame]:
    n99 = read_table(INPUTS["n99_adjudicated"])
    n99_scores = read_table(INPUTS["n99_recovered_scores"])
    n99_submitted = read_table(INPUTS["n99_submitted_correlations"])
    n99_submitted_boot = read_table(INPUTS["n99_submitted_bootstrap"])
    n100 = read_table(INPUTS["n100_adjudicated"])
    n100_submitted = read_table(INPUTS["n100_submitted_correlations"])
    n100_submitted_binary = read_table(INPUTS["n100_submitted_binary"])
    n100_submitted_boot = read_table(INPUTS["n100_submitted_bootstrap"])

    n99_score_columns = ["auto_deberta", "auto_second_nli", "auto_ragas"]
    n99_merged = n99[["id", "adjudicated_label"]].merge(
        n99_scores[["id", *n99_score_columns]], on="id", validate="one_to_one"
    )
    n99_y = n99_merged["adjudicated_label"].map(
        {"unsupported": 0.0, "partially_supported": 0.5, "supported": 1.0}
    ).to_numpy(dtype=float)
    n100_y = n100["adjudicated_label"].map(
        {"hallucinated": 0.0, "unclear": 0.5, "faithful": 1.0}
    ).to_numpy(dtype=float)

    rows = []
    for panel, frame, y, columns in [
        (
            "n99_typical",
            n99_merged,
            n99_y,
            ["auto_deberta", "auto_second_nli", "auto_ragas"],
        ),
        (
            "n100_disagreement_targeted",
            n100,
            n100_y,
            ["deberta_score", "second_nli_score", "ragas_style_score"],
        ),
    ]:
        for column in columns:
            score = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
            for metric in ["pearson", "spearman", "kendall"]:
                estimate = safe_corr(y, score, metric)
                rows.append(
                    {
                        "panel": panel,
                        "scorer": SCORER_DISPLAY[column],
                        "metric": metric,
                        "estimate": estimate,
                        "ci_lower": np.nan,
                        "ci_upper": np.nan,
                        "n": int(np.sum(np.isfinite(y) & np.isfinite(score))),
                        "endpoint": "adjudicated_ordinal",
                        "positive_label": "",
                        "indeterminate_excluded": 0,
                        "ci_source": "",
                    }
                )

    metrics_df = pd.DataFrame(rows)

    n99_metric_map = {
        "auto_deberta": "legacy_deberta_proxy",
        "auto_second_nli": "legacy_second_nli_proxy",
        "auto_ragas": "ragas_style_judge",
    }
    for _, submitted_row in n99_submitted.iterrows():
        scorer = n99_metric_map[submitted_row["metric"]]
        for metric, submitted_column in [
            ("pearson", "pearson_r"),
            ("spearman", "spearman_rho"),
            ("kendall", "kendall_tau_b"),
        ]:
            actual = metrics_df.query(
                "panel == 'n99_typical' and scorer == @scorer and metric == @metric"
            )["estimate"].iloc[0]
            assert_close(
                actual,
                float(submitted_row[submitted_column]),
                f"n99 {scorer} {metric}",
            )

    for _, submitted_row in n100_submitted.iterrows():
        scorer = SCORER_DISPLAY[submitted_row["scorer"]]
        metric = str(submitted_row["metric"])
        actual = metrics_df.query(
            "panel == 'n100_disagreement_targeted' and scorer == @scorer and metric == @metric"
        )["estimate"].iloc[0]
        assert_close(actual, float(submitted_row["value"]), f"n100 {scorer} {metric}")

    submitted_names = {
        "DeBERTa-v3 NLI": "legacy_deberta_proxy",
        "Second NLI": "legacy_second_nli_proxy",
        "RAGAS-style judge": "ragas_style_judge",
    }
    n99_boot = n99_submitted_boot.query("table == '6_human_calibration'")
    for _, boot_row in n99_boot.iterrows():
        scorer = submitted_names[boot_row["item"]]
        metric = "pearson" if boot_row["statistic"] == "pearson_r" else "spearman"
        selector = (
            (metrics_df["panel"] == "n99_typical")
            & (metrics_df["scorer"] == scorer)
            & (metrics_df["metric"] == metric)
        )
        metrics_df.loc[selector, ["ci_lower", "ci_upper", "ci_source"]] = [
            float(boot_row["ci_low"]),
            float(boot_row["ci_high"]),
            "submitted_fixed_output_10000_bootstrap_seed_20260429",
        ]

    for _, boot_row in n100_submitted_boot.query("metric_group == 'correlation'").iterrows():
        scorer = SCORER_DISPLAY[boot_row["scorer"]]
        metric = str(boot_row["metric_name"])
        selector = (
            (metrics_df["panel"] == "n100_disagreement_targeted")
            & (metrics_df["scorer"] == scorer)
            & (metrics_df["metric"] == metric)
        )
        metrics_df.loc[selector, ["ci_lower", "ci_upper", "ci_source"]] = [
            float(boot_row["ci_lower"]),
            float(boot_row["ci_upper"]),
            "submitted_fixed_output_1000_bootstrap",
        ]

    binary_rows = []
    n100_binary_y = (n100_y == 1.0).astype(float)
    for column in ["deberta_score", "second_nli_score", "ragas_style_score"]:
        scorer = SCORER_DISPLAY[column]
        score = n100[column].to_numpy(dtype=float)
        submitted = n100_submitted_binary.query("scorer == @column").iloc[0]
        for metric, submitted_col in [
            ("auroc", "auroc"),
            ("average_precision", "auprc"),
        ]:
            estimate = safe_auc(n100_binary_y, score, metric)
            assert_close(
                estimate,
                float(submitted[submitted_col]),
                f"n100 {scorer} {metric}",
            )
            submitted_metric_name = "auprc" if metric == "average_precision" else metric
            boot = n100_submitted_boot.query(
                "metric_group == 'binary_metric' and scorer == @column and metric_name == @submitted_metric_name"
            ).iloc[0]
            binary_rows.append(
                {
                    "panel": "n100_disagreement_targeted",
                    "scorer": scorer,
                    "metric": metric,
                    "estimate": estimate,
                    "ci_lower": float(boot["ci_lower"]),
                    "ci_upper": float(boot["ci_upper"]),
                    "n": len(n100),
                    "endpoint": "adjudicated_binary",
                    "positive_label": "faithful=1",
                    "indeterminate_excluded": 0,
                    "ci_source": "submitted_fixed_output_1000_bootstrap",
                }
            )

    determinate = np.isin(n99_y, [0.0, 1.0])
    n99_binary_y = n99_y[determinate]
    for column in ["auto_deberta", "auto_second_nli", "auto_ragas"]:
        scorer = SCORER_DISPLAY[column]
        score = n99_merged.loc[determinate, column].to_numpy(dtype=float)
        for offset, metric in enumerate(["auroc", "average_precision"], start=20):
            estimate = safe_auc(n99_binary_y, score, metric)
            lower, upper, valid = bootstrap_single(
                [n99_binary_y, score],
                lambda y, s, m=metric: safe_auc(y, s, m),
                seed=SEED + offset,
            )
            binary_rows.append(
                {
                    "panel": "n99_typical",
                    "scorer": scorer,
                    "metric": metric,
                    "estimate": estimate,
                    "ci_lower": lower,
                    "ci_upper": upper,
                    "n": int(determinate.sum()),
                    "endpoint": "secondary_determinate_binary",
                    "positive_label": "supported=1",
                    "indeterminate_excluded": int((~determinate).sum()),
                    "ci_source": f"prompt03_{N_BOOTSTRAP}_bootstrap_seed_{SEED + offset};valid={valid}",
                }
            )

    metrics_df = pd.concat([metrics_df, pd.DataFrame(binary_rows)], ignore_index=True)

    ranking_rows = []
    ranking_specs = [
        (
            "n99_typical",
            n99_merged,
            n99_y,
            ["auto_deberta", "auto_second_nli", "auto_ragas"],
        ),
        (
            "n100_disagreement_targeted",
            n100,
            n100_y,
            ["deberta_score", "second_nli_score", "ragas_style_score"],
        ),
    ]
    for panel_index, (panel, frame, y, columns) in enumerate(ranking_specs):
        for pair_index, (column_a, column_b) in enumerate(
            [
                (columns[1], columns[0]),
                (columns[2], columns[0]),
                (columns[2], columns[1]),
            ]
        ):
            score_a = frame[column_a].to_numpy(dtype=float)
            score_b = frame[column_b].to_numpy(dtype=float)
            estimate = safe_corr(y, score_a, "spearman") - safe_corr(
                y, score_b, "spearman"
            )
            lower, upper, valid = bootstrap_single(
                [y, score_a, score_b],
                lambda labels, a, b: safe_corr(labels, a, "spearman")
                - safe_corr(labels, b, "spearman"),
                seed=SEED + 100 + panel_index * 10 + pair_index,
            )
            ranking_rows.append(
                {
                    "panel": panel,
                    "scorer_a": SCORER_DISPLAY[column_a],
                    "scorer_b": SCORER_DISPLAY[column_b],
                    "metric": "spearman_difference_a_minus_b",
                    "estimate": estimate,
                    "ci_lower": lower,
                    "ci_upper": upper,
                    "n": len(frame),
                    "valid_bootstrap_samples": valid,
                    "classification": (
                        "stable_order"
                        if lower > 0 or upper < 0
                        else "ranking_uncertain"
                    ),
                }
            )

    return metrics_df, pd.DataFrame(ranking_rows)


def analyze_context_outputs() -> pd.DataFrame:
    frame = read_table(INPUTS["context_n600"]).copy()
    expected_counts = frame.groupby("condition").size().to_dict()
    if expected_counts != {"baseline": 200, "hcpc_v1": 200, "hcpc_v2": 200}:
        raise AssertionError(f"Unexpected context panel condition counts: {expected_counts}")

    ordered = {}
    for condition in ["baseline", "hcpc_v1", "hcpc_v2"]:
        ordered[condition] = frame.query("condition == @condition").reset_index(drop=True)
    if not ordered["baseline"]["question"].equals(ordered["hcpc_v1"]["question"]):
        raise AssertionError("Context panel baseline and HCPC-v1 questions are not paired.")

    columns = {
        "legacy_deberta_proxy": "faith_deberta",
        "context_conditioned_deberta": "faith_deberta_ctx",
        "legacy_second_nli_proxy": "faith_second_nli",
        "context_conditioned_second_nli": "faith_roberta_mnli_ctx",
        "ragas_style_judge": "faith_ragas",
    }
    rows = []
    for scorer_index, (scorer, column) in enumerate(columns.items()):
        baseline = ordered["baseline"][column].to_numpy(dtype=float)
        hcpc_v1 = ordered["hcpc_v1"][column].to_numpy(dtype=float)
        valid = np.isfinite(baseline) & np.isfinite(hcpc_v1)
        differences = baseline[valid] - hcpc_v1[valid]
        estimate = float(np.mean(differences))
        lower, upper, valid_boot = bootstrap_single(
            [differences],
            lambda values: float(np.mean(values)),
            seed=SEED + 200 + scorer_index,
        )
        rows.append(
            {
                "analysis": "baseline_minus_hcpc_v1",
                "scorer": scorer,
                "comparator": "",
                "estimate": estimate,
                "ci_lower": lower,
                "ci_upper": upper,
                "n_pairs": int(valid.sum()),
                "valid_bootstrap_samples": valid_boot,
                "interpretation": "positive_means_baseline_scores_higher",
            }
        )

    comparison_pairs = [
        (
            "context_conditioned_deberta",
            "faith_deberta_ctx",
            "legacy_deberta_proxy",
            "faith_deberta",
        ),
        (
            "context_conditioned_second_nli",
            "faith_roberta_mnli_ctx",
            "legacy_second_nli_proxy",
            "faith_second_nli",
        ),
    ]
    for pair_index, (context_name, context_col, legacy_name, legacy_col) in enumerate(
        comparison_pairs
    ):
        arrays = [
            ordered["baseline"][context_col].to_numpy(dtype=float),
            ordered["hcpc_v1"][context_col].to_numpy(dtype=float),
            ordered["baseline"][legacy_col].to_numpy(dtype=float),
            ordered["hcpc_v1"][legacy_col].to_numpy(dtype=float),
        ]
        valid = np.logical_and.reduce([np.isfinite(array) for array in arrays])
        contrast_difference = (
            arrays[0][valid]
            - arrays[1][valid]
            - (arrays[2][valid] - arrays[3][valid])
        )
        estimate = float(np.mean(contrast_difference))
        lower, upper, valid_boot = bootstrap_single(
            [contrast_difference],
            lambda values: float(np.mean(values)),
            seed=SEED + 220 + pair_index,
        )
        rows.append(
            {
                "analysis": "context_minus_legacy_contrast_difference",
                "scorer": context_name,
                "comparator": legacy_name,
                "estimate": estimate,
                "ci_lower": lower,
                "ci_upper": upper,
                "n_pairs": int(valid.sum()),
                "valid_bootstrap_samples": valid_boot,
                "interpretation": "difference_of_baseline_minus_hcpc_v1_contrasts",
            }
        )
    return pd.DataFrame(rows)


def analyze_thresholds() -> pd.DataFrame:
    tau = read_table(INPUTS["threshold_tau_summary"])
    transfer = read_table(INPUTS["threshold_transfer_matrix"])
    target_columns = ["squad", "pubmedqa", "hotpotqa", "naturalqs", "triviaqa"]
    rows = []
    for _, row in transfer.iterrows():
        values = row[target_columns].to_numpy(dtype=float)
        rows.append(
            {
                "analysis": "selected_tau_transfer",
                "selector": row["tune_dataset"],
                "tau": float(row["tau"]),
                "target": "five_target_summary",
                "estimate": float(np.mean(values)),
                "minimum": float(np.min(values)),
                "maximum": float(np.max(values)),
                "range": float(np.ptp(values)),
                "positive_cells": int(np.sum(values > 0)),
                "total_cells": len(values),
            }
        )
    for dataset, subset in tau.groupby("dataset", sort=True):
        values = subset["recovery"].to_numpy(dtype=float)
        best_row = subset.loc[subset["recovery"].idxmax()]
        worst_row = subset.loc[subset["recovery"].idxmin()]
        rows.append(
            {
                "analysis": "within_dataset_tau_sensitivity",
                "selector": dataset,
                "tau": np.nan,
                "target": dataset,
                "estimate": float(np.mean(values)),
                "minimum": float(worst_row["recovery"]),
                "maximum": float(best_row["recovery"]),
                "range": float(np.ptp(values)),
                "positive_cells": int(np.sum(values > 0)),
                "total_cells": len(values),
            }
        )
    return pd.DataFrame(rows)


def analyze_pareto_and_cost() -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = read_table(INPUTS["pareto_summary"]).copy()
    if len(summary) != 6 or not (summary["n"] == 200).all():
        raise AssertionError("Unexpected fixed Pareto summary shape or sample sizes.")
    summary["indexing_s"] = np.where(
        summary["condition"].eq("raptor_2l"),
        summary["raptor_index_s"],
        summary["base_index_s"],
    )
    pareto_rows = []
    for dataset, subset in summary.groupby("dataset", sort=True):
        for _, candidate in subset.iterrows():
            dominated_by = []
            for _, competitor in subset.iterrows():
                if competitor["condition"] == candidate["condition"]:
                    continue
                weakly_better = (
                    competitor["faithfulness"] >= candidate["faithfulness"]
                    and competitor["mean_latency_ms"] <= candidate["mean_latency_ms"]
                    and competitor["indexing_s"] <= candidate["indexing_s"]
                )
                strictly_better = (
                    competitor["faithfulness"] > candidate["faithfulness"]
                    or competitor["mean_latency_ms"] < candidate["mean_latency_ms"]
                    or competitor["indexing_s"] < candidate["indexing_s"]
                )
                if weakly_better and strictly_better:
                    dominated_by.append(str(competitor["condition"]))
            pareto_rows.append(
                {
                    "dataset": dataset,
                    "system": candidate["condition"],
                    "n": int(candidate["n"]),
                    "faithfulness": float(candidate["faithfulness"]),
                    "faith_ci_lower": float(candidate["faith_ci95_lo"]),
                    "faith_ci_upper": float(candidate["faith_ci95_hi"]),
                    "mean_latency_ms": float(candidate["mean_latency_ms"]),
                    "indexing_s": float(candidate["indexing_s"]),
                    "pareto_frontier": not dominated_by,
                    "dominated_by": ";".join(dominated_by),
                }
            )

    weights = [0.0, 0.01, 0.025, 0.05]
    query_volumes = [200, 1_000, 10_000]
    cost_rows = []
    for dataset, subset in summary.groupby("dataset", sort=True):
        for volume in query_volumes:
            for weight in weights:
                working = subset.copy()
                working["amortized_time_s"] = (
                    working["mean_latency_ms"] / 1000.0
                    + working["indexing_s"] / volume
                )
                working["utility"] = (
                    working["faithfulness"] - weight * working["amortized_time_s"]
                )
                maximum = working["utility"].max()
                for _, row in working.iterrows():
                    cost_rows.append(
                        {
                            "dataset": dataset,
                            "query_volume": volume,
                            "time_penalty_faithfulness_per_second": weight,
                            "system": row["condition"],
                            "faithfulness": float(row["faithfulness"]),
                            "amortized_time_s": float(row["amortized_time_s"]),
                            "utility": float(row["utility"]),
                            "best_at_setting": bool(
                                np.isclose(row["utility"], maximum, atol=1e-12)
                            ),
                        }
                    )
    return pd.DataFrame(pareto_rows), pd.DataFrame(cost_rows)


def build_coverage() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "panel": "human_typical",
                "rows": 99,
                "coverage": "33 rows per condition",
                "role": "typical-slice human calibration",
                "limitation": "small ordinal panel; only 4 unsupported adjudicated labels",
            },
            {
                "panel": "human_disagreement_targeted",
                "rows": 100,
                "coverage": "34 baseline; 33 HCPC-v1; 33 HCPC-v2",
                "role": "stress-test scorer disagreement",
                "limitation": "selection is disagreement-targeted and not prevalence-representative",
            },
            {
                "panel": "fixed_multimetric_main",
                "rows": 7500,
                "coverage": "fixed existing outputs",
                "role": "main scorer and condition summaries",
                "limitation": "historical answer-only NLI proxies",
            },
            {
                "panel": "matched_control",
                "rows": 2500,
                "coverage": "fixed matched query control",
                "role": "paired condition comparison",
                "limitation": "do not use stale matched-binary p=0.011",
            },
            {
                "panel": "context_conditioned_nli",
                "rows": 600,
                "coverage": "200 per condition; 194 complete baseline/HCPC-v1 pairs",
                "role": "fixed-context re-encoding sensitivity",
                "limitation": "not fresh retrieval or generation; subset only",
            },
            {
                "panel": "threshold_transfer",
                "rows": 25,
                "coverage": "5 datasets x 5 tau values; 5 selected transfer rules",
                "role": "threshold sensitivity and transfer",
                "limitation": "descriptive fixed-output grid",
            },
            {
                "panel": "faith_latency_indexing",
                "rows": 1200,
                "coverage": "2 datasets x 3 systems x 200 rows",
                "role": "deployment trade-off sensitivity",
                "limitation": "two datasets; utility weights are illustrative",
            },
        ]
    )


def build_human_safe_numbers(
    agreement: pd.DataFrame, metrics: pd.DataFrame
) -> pd.DataFrame:
    rows = []
    for _, row in agreement.iterrows():
        rows.append(
            {
                "panel": row["panel"],
                "claim_id": f"{row['panel']}_{row['metric']}",
                "metric": row["metric"],
                "scorer": "",
                "estimate": row["estimate"],
                "ci_lower": row["ci_lower"],
                "ci_upper": row["ci_upper"],
                "n": row["n"],
                "endpoint_or_convention": "pre-adjudication labels; unweighted kappa",
                "status": "verified_rebuttal_safe",
            }
        )
    keep_metrics = metrics[
        metrics["metric"].isin(
            ["spearman", "auroc", "average_precision"]
        )
    ]
    for _, row in keep_metrics.iterrows():
        convention = row["endpoint"]
        if row["metric"] == "average_precision":
            convention += (
                "; sklearn average_precision_score; higher score=positive; "
                + row["positive_label"]
            )
        rows.append(
            {
                "panel": row["panel"],
                "claim_id": (
                    f"{row['panel']}_{row['scorer']}_{row['metric']}_{row['endpoint']}"
                ),
                "metric": row["metric"],
                "scorer": row["scorer"],
                "estimate": row["estimate"],
                "ci_lower": row["ci_lower"],
                "ci_upper": row["ci_upper"],
                "n": row["n"],
                "endpoint_or_convention": convention,
                "status": (
                    "verified_rebuttal_safe_secondary"
                    if row["endpoint"] == "secondary_determinate_binary"
                    else "verified_rebuttal_safe"
                ),
            }
        )
    return pd.DataFrame(rows)


def build_new_safe_numbers(
    ranking: pd.DataFrame,
    context: pd.DataFrame,
    threshold: pd.DataFrame,
    pareto: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for _, row in ranking.iterrows():
        rows.append(
            {
                "analysis": "scorer_ranking_uncertainty",
                "claim_id": f"{row['panel']}_{row['scorer_a']}_minus_{row['scorer_b']}",
                "estimate": row["estimate"],
                "ci_lower": row["ci_lower"],
                "ci_upper": row["ci_upper"],
                "n": row["n"],
                "unit": "Spearman rho difference",
                "scope": row["panel"],
                "status": (
                    "verified_rebuttal_safe"
                    if row["classification"] == "stable_order"
                    else "verified_conditional"
                ),
            }
        )
    for _, row in context.iterrows():
        rows.append(
            {
                "analysis": row["analysis"],
                "claim_id": f"context_{row['scorer']}_{row['analysis']}",
                "estimate": row["estimate"],
                "ci_lower": row["ci_lower"],
                "ci_upper": row["ci_upper"],
                "n": row["n_pairs"],
                "unit": "mean score contrast",
                "scope": "fixed-context re-encoding subset",
                "status": "verified_conditional",
            }
        )
    for _, row in threshold.query("analysis == 'selected_tau_transfer'").iterrows():
        rows.append(
            {
                "analysis": "threshold_transfer",
                "claim_id": f"threshold_transfer_{row['selector']}",
                "estimate": row["estimate"],
                "ci_lower": row["minimum"],
                "ci_upper": row["maximum"],
                "n": row["total_cells"],
                "unit": "recovery index across targets",
                "scope": f"tau={row['tau']}; five fixed target datasets",
                "status": "verified_conditional",
            }
        )
    for dataset, subset in pareto.groupby("dataset", sort=True):
        frontier = ";".join(subset.loc[subset["pareto_frontier"], "system"].astype(str))
        rows.append(
            {
                "analysis": "pareto_frontier",
                "claim_id": f"pareto_{dataset}",
                "estimate": np.nan,
                "ci_lower": np.nan,
                "ci_upper": np.nan,
                "n": int(subset["n"].sum()),
                "unit": f"frontier={frontier}",
                "scope": f"{dataset}; faithfulness maximize, latency/indexing minimize",
                "status": "verified_conditional",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    HUMAN_OUT.mkdir(parents=True, exist_ok=True)
    RESULTS_OUT.mkdir(parents=True, exist_ok=True)

    input_manifest = verify_inputs()
    diagnostics, distributions, agreement = verify_human_panels()
    metrics, ranking = verify_human_metrics()
    context = analyze_context_outputs()
    threshold = analyze_thresholds()
    pareto, cost = analyze_pareto_and_cost()
    coverage = build_coverage()
    human_safe = build_human_safe_numbers(agreement, metrics)
    new_safe = build_new_safe_numbers(ranking, context, threshold, pareto)

    tables = {
        RESULTS_OUT / "input_manifest.csv": input_manifest,
        RESULTS_OUT / "human_slice_diagnostics.csv": diagnostics,
        RESULTS_OUT / "human_label_distributions.csv": distributions,
        RESULTS_OUT / "human_agreement_bootstrap.csv": agreement,
        RESULTS_OUT / "human_metric_verification.csv": metrics,
        RESULTS_OUT / "scorer_ranking_bootstrap.csv": ranking,
        RESULTS_OUT / "context_conditioned_comparison.csv": context,
        RESULTS_OUT / "threshold_sensitivity.csv": threshold,
        RESULTS_OUT / "pareto_frontier.csv": pareto,
        RESULTS_OUT / "cost_weight_sensitivity.csv": cost,
        RESULTS_OUT / "sample_size_coverage.csv": coverage,
        HUMAN_OUT / "HUMAN_EVAL_SAFE_NUMBERS.csv": human_safe,
        ANALYSIS_OUT / "NEW_REBUTTAL_SAFE_NUMBERS.csv": new_safe,
    }
    for path, table in tables.items():
        table.to_csv(path, index=False, float_format="%.9f")

    runtime = {
        "status": "PASS",
        "seed": SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "no_model_inference": True,
        "no_network_access": True,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "outputs": [path.relative_to(WORKSPACE).as_posix() for path in tables],
    }
    (RESULTS_OUT / "analysis_run_manifest.json").write_text(
        json.dumps(runtime, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(runtime, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"PROMPT03_ANALYSIS_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
