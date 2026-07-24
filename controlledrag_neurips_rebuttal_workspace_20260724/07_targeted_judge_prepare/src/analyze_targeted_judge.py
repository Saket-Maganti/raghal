
"""Run only preregistered modern-judge analyses."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import (
    average_precision_score, balanced_accuracy_score, brier_score_loss,
    confusion_matrix, f1_score, precision_score, recall_score
)

SEED = 20260724
N_BOOT = 10000

def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]

def csv_rows(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["status"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows or [{"status": "no_rows"}])

def percentile(values: list[float]) -> tuple[float, float]:
    values = [v for v in values if np.isfinite(v)]
    if not values:
        return float("nan"), float("nan")
    return tuple(float(x) for x in np.percentile(values, [2.5, 97.5]))

def paired_bootstrap_diff(a: np.ndarray, b: np.ndarray, fn, seed_offset: int = 0):
    rng = np.random.default_rng(SEED + seed_offset)
    values = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(a), len(a))
        values.append(float(fn(a[idx]) - fn(b[idx])))
    return percentile(values)

def calibration(y: np.ndarray, scores: np.ndarray, flags: np.ndarray) -> dict:
    pred = flags.astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "n": len(y),
        "spearman": float(spearmanr(scores, y).statistic),
        "average_precision_faithful_1": float(average_precision_score(y, scores)),
        "boolean_accuracy": float((pred == y).mean()),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "brier": float(brier_score_loss(y, scores / 100.0)),
    }

def analyze(bundle_root: str | Path, output_root: str | Path) -> dict:
    bundle, output = Path(bundle_root), Path(output_root)
    rows = {r["experiment_row_id"]: r for r in jsonl(bundle / "manifests/all_frozen_rows.jsonl")}
    records = jsonl(output / "raw_outputs/merged_outputs.jsonl")
    scores = {}
    for record in records:
        if record["valid"]:
            scores[(record["experiment_row_id"], record["interface"])] = record["parsed_output"]
    eligible_pairs = {
        r["pair_id"] for r in csv_rows(bundle / "manifests/PAIR_COMPLETENESS.csv")
        if r["primary_pair_eligible"] == "true"
    }
    pair_members = {}
    for row in rows.values():
        if row["panel"] == "main_600" and row["pair_id"] in eligible_pairs:
            pair_members.setdefault(row["pair_id"], {})[row["system"]] = row["experiment_row_id"]
    contrasts, bootstrap_rows = [], []
    per_interface_diffs = {}
    for interface in ("answer_only", "context_conditioned"):
        pair_scores = []
        for pair_id in sorted(eligible_pairs):
            members = pair_members[pair_id]
            b = scores[(members["baseline"], interface)]["faithfulness_score"]
            h = scores[(members["hcpc_v1"], interface)]["faithfulness_score"]
            pair_scores.append((b, h))
        arr = np.array(pair_scores, dtype=float)
        diffs = arr[:, 0] - arr[:, 1]
        rng = np.random.default_rng(SEED)
        boots = [float(diffs[rng.integers(0, len(diffs), len(diffs))].mean()) for _ in range(N_BOOT)]
        lo, hi = percentile(boots)
        per_interface_diffs[interface] = diffs
        contrasts.append({
            "interface": interface, "n_pairs": len(diffs),
            "baseline_mean": float(arr[:, 0].mean()), "hcpc_v1_mean": float(arr[:, 1].mean()),
            "baseline_minus_hcpc_v1": float(diffs.mean()), "ci_low": lo, "ci_high": hi
        })
        bootstrap_rows.append({
            "analysis": "main_contrast", "interface": interface, "estimate": float(diffs.mean()),
            "ci_low": lo, "ci_high": hi, "replicates": N_BOOT, "seed": SEED
        })
    delta = per_interface_diffs["context_conditioned"] - per_interface_diffs["answer_only"]
    rng = np.random.default_rng(SEED)
    delta_boot = [float(delta[rng.integers(0, len(delta), len(delta))].mean()) for _ in range(N_BOOT)]
    dlo, dhi = percentile(delta_boot)
    interface_differences = [{
        "analysis": "difference_in_main_contrasts",
        "estimate": float(delta.mean()), "ci_low": dlo, "ci_high": dhi,
        "material_threshold": 5.0
    }]
    calibration_files = {}
    for panel, filename in (
        ("human_typical", "HUMAN_TYPICAL_CALIBRATION.csv"),
        ("human_disagreement", "HUMAN_DISAGREEMENT_CALIBRATION.csv"),
    ):
        ids = sorted(r["experiment_row_id"] for r in rows.values() if r["panel"] == panel)
        out_rows = []
        arrays = {}
        for interface in ("answer_only", "context_conditioned"):
            y = np.array([rows[i]["human_label"] for i in ids], dtype=int)
            s = np.array([scores[(i, interface)]["faithfulness_score"] for i in ids], dtype=float)
            f = np.array([scores[(i, interface)]["faithful"] for i in ids], dtype=bool)
            metric = calibration(y, s, f)
            metric.update({"panel": panel, "interface": interface, "valid_output_rate": 1.0})
            out_rows.append(metric)
            arrays[interface] = (y, s)
        y, a = arrays["answer_only"]
        _, c = arrays["context_conditioned"]
        rng = np.random.default_rng(SEED)
        ap_diffs, rho_diffs = [], []
        for _ in range(N_BOOT):
            idx = rng.integers(0, len(y), len(y))
            yy, aa, cc = y[idx], a[idx], c[idx]
            if len(np.unique(yy)) < 2:
                continue
            ap_diffs.append(average_precision_score(yy, cc) - average_precision_score(yy, aa))
            rho_diffs.append(spearmanr(cc, yy).statistic - spearmanr(aa, yy).statistic)
        for metric_name, vals in (("ap_difference_context_minus_answer", ap_diffs), ("spearman_difference_context_minus_answer", rho_diffs)):
            lo, hi = percentile(vals)
            interface_differences.append({
                "analysis": f"{panel}_{metric_name}", "estimate": float(np.mean(vals)),
                "ci_low": lo, "ci_high": hi, "material_threshold": ""
            })
            bootstrap_rows.append({
                "analysis": f"{panel}_{metric_name}", "interface": "context_minus_answer",
                "estimate": float(np.mean(vals)), "ci_low": lo, "ci_high": hi,
                "replicates": N_BOOT, "seed": SEED
            })
        calibration_files[filename] = out_rows
    analysis_dir = output / "analysis"
    write_csv(analysis_dir / "MAIN_SYSTEM_CONTRASTS.csv", contrasts)
    for filename, rows_out in calibration_files.items():
        write_csv(analysis_dir / filename, rows_out)
    write_csv(analysis_dir / "INTERFACE_DIFFERENCES.csv", interface_differences)
    write_csv(analysis_dir / "BOOTSTRAP_INTERVALS.csv", bootstrap_rows)
    answer_contrast = contrasts[0]["baseline_minus_hcpc_v1"]
    context_contrast = contrasts[1]["baseline_minus_hcpc_v1"]
    opposite = answer_contrast * context_contrast < 0
    material = abs(context_contrast - answer_contrast) >= 5.0
    if opposite:
        contrast_pattern = "sign reversal"
    elif material:
        contrast_pattern = "same sign / material magnitude change"
    elif answer_contrast == 0 or context_contrast == 0:
        contrast_pattern = "indeterminate"
    else:
        contrast_pattern = "same sign / small change"
    typical_metrics = calibration_files["HUMAN_TYPICAL_CALIBRATION.csv"]
    disagreement_metrics = calibration_files["HUMAN_DISAGREEMENT_CALIBRATION.csv"]
    typical_preference = max(typical_metrics, key=lambda r: r["average_precision_faithful_1"])["interface"]
    disagreement_preference = max(
        disagreement_metrics, key=lambda r: r["average_precision_faithful_1"]
    )["interface"]
    claim_rows = [
        {
            "claim": "baseline_vs_hcpc_v1_under_scorer_input",
            "classification": "Conditional" if opposite or material else "Stable",
            "evidence": contrast_pattern,
        },
        {
            "claim": "scorer_ranking_across_human_slices",
            "classification": (
                "Conditional" if typical_preference != disagreement_preference else "Stable"
            ),
            "evidence": (
                f"typical_prefers={typical_preference};"
                f"disagreement_diagnostic_prefers={disagreement_preference}"
            ),
        },
        {
            "claim": "threshold_portability",
            "classification": "Conditional",
            "evidence": "existing evidence; not retested by targeted judge",
        },
        {
            "claim": "quality_cost_decision",
            "classification": "Conditional",
            "evidence": "existing evidence; not retested by targeted judge",
        },
        {
            "claim": "modern_open_weight_judge_relevance",
            "classification": "Stable" if opposite or material else "Unresolved",
            "evidence": contrast_pattern,
        },
    ]
    write_csv(analysis_dir / "CLAIM_STABILITY_TABLE.csv", claim_rows)
    summary = {
        "status": "PREREGISTERED_ANALYSIS_COMPLETE",
        "bootstrap_replicates": N_BOOT, "seed": SEED, "main_pairs": len(eligible_pairs),
        "typical_rows": sum(r["panel"] == "human_typical" for r in rows.values()),
        "disagreement_rows": sum(r["panel"] == "human_disagreement" for r in rows.values()),
        "contrast_pattern": contrast_pattern,
    }
    (analysis_dir / "RESULTS_SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_root")
    parser.add_argument("output_root")
    args = parser.parse_args()
    print(json.dumps(analyze(args.bundle_root, args.output_root), indent=2))

if __name__ == "__main__":
    main()
