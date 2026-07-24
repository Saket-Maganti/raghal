"""
train_mech_classifier.py — Item 4 (Upgrade Wave 1a)
====================================================

Treats the per-layer mechanistic signals produced by
`experiments/run_mechanistic_analysis.py` (attention entropy, retrieved
mass, parametric mass) as feature vectors and trains a lightweight
classifier to predict whether a context was coherent or fragmented.

This converts the mechanistic analysis from a descriptive aid into a
standalone hallucination-detection contribution: if the classifier
achieves AUC substantially above a chance or NLI-only baseline, we can
claim that internal-model signals carry hallucination information the
output-layer NLI detector misses.

Inputs (from results/mechanistic/):
  per_pair.csv                — one row per (pair_id, condition) with
                                 aggregate entropy / retrieved-mass.
  entropy_by_layer.csv        — long-form per-layer entropy.
  retrieved_mass_by_layer.csv — long-form per-layer retrieved mass.

Outputs (results/mech_classifier/):
  features.csv                — wide feature matrix used for training.
  cv_results.csv              — per-fold AUC / F1 for each classifier.
  feature_importance.csv      — L1-logistic coefficients (standardized).
  summary.md                  — headline table + narrative.

Runs in ~30 s on the M4 (no GPU).  Depends only on scikit-learn.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import os
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler


MECH_DIR   = "results/mechanistic"
OUTPUT_DIR = "results/mech_classifier"


# ── Feature construction ──────────────────────────────────────────────────────

def _load_per_layer(path: str, value_col: str) -> pd.DataFrame:
    """Pivot long-form per-layer CSV into a wide (pair, condition) matrix."""
    df = pd.read_csv(path)
    if df.empty:
        return df
    return df.pivot_table(
        index=["pair_id", "category", "condition"],
        columns="layer",
        values=value_col,
    ).add_prefix(f"{value_col}_L").reset_index()


def _aggregate_stats(df_long: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Per-(pair, condition) summary statistics across layers."""
    if df_long.empty:
        return df_long
    g = df_long.groupby(["pair_id", "category", "condition"])[value_col]
    out = g.agg(["mean", "std", "min", "max",
                 lambda s: float(np.percentile(s, 25)),
                 lambda s: float(np.percentile(s, 75)),
                 lambda s: float(s.iloc[-3:].mean()) if len(s) >= 3 else float(s.mean()),
                 lambda s: float(s.iloc[:3].mean())  if len(s) >= 3 else float(s.mean())])
    out.columns = [f"{value_col}_{n}" for n in
                   ("mean", "std", "min", "max", "p25", "p75",
                    "last3mean", "first3mean")]
    return out.reset_index()


def build_features() -> pd.DataFrame:
    ent_long  = pd.read_csv(os.path.join(MECH_DIR, "entropy_by_layer.csv"))
    mass_long = pd.read_csv(os.path.join(MECH_DIR, "retrieved_mass_by_layer.csv"))
    pair_df   = pd.read_csv(os.path.join(MECH_DIR, "per_pair.csv"))

    ent_wide  = _load_per_layer(os.path.join(MECH_DIR, "entropy_by_layer.csv"),
                                "mean_entropy")
    mass_wide = _load_per_layer(os.path.join(MECH_DIR, "retrieved_mass_by_layer.csv"),
                                "mean_retrieved_mass")

    ent_stats  = _aggregate_stats(ent_long,  "mean_entropy")
    mass_stats = _aggregate_stats(mass_long, "mean_retrieved_mass")

    # Bring in top-level per-pair features (aggregate signal).
    pair_feats = pair_df[[
        "pair_id", "category", "condition",
        "mean_entropy", "mean_retrieved_mass", "mean_parametric_mass",
        "p25_retrieved_mass", "p75_retrieved_mass",
        "input_tokens", "output_tokens",
    ]].copy()
    pair_feats = pair_feats.rename(columns={
        "mean_entropy":         "agg_mean_entropy",
        "mean_retrieved_mass":  "agg_mean_retrieved_mass",
        "mean_parametric_mass": "agg_mean_parametric_mass",
        "p25_retrieved_mass":   "agg_p25_retrieved_mass",
        "p75_retrieved_mass":   "agg_p75_retrieved_mass",
    })

    keys = ["pair_id", "category", "condition"]
    feats = pair_feats \
        .merge(ent_stats,  on=keys, how="left") \
        .merge(mass_stats, on=keys, how="left") \
        .merge(ent_wide,   on=keys, how="left") \
        .merge(mass_wide,  on=keys, how="left")
    return feats


# ── Training / evaluation ─────────────────────────────────────────────────────

def _label_fragmented(df: pd.DataFrame) -> np.ndarray:
    return (df["condition"] == "fragmented").astype(int).values


def _feature_matrix(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    drop = {"pair_id", "category", "condition"}
    cols = [c for c in df.columns if c not in drop]
    X = df[cols].to_numpy(dtype=np.float64)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    return X, cols


def stratified_cv(
    X: np.ndarray, y: np.ndarray, clf, n_splits: int = 5, seed: int = 42,
) -> Dict[str, float]:
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    aucs, f1s, accs = [], [], []
    for tr, te in skf.split(X, y):
        scaler = StandardScaler().fit(X[tr])
        Xtr, Xte = scaler.transform(X[tr]), scaler.transform(X[te])
        clf_ = clf.__class__(**clf.get_params())
        clf_.fit(Xtr, y[tr])
        if hasattr(clf_, "predict_proba"):
            proba = clf_.predict_proba(Xte)[:, 1]
        else:
            proba = clf_.decision_function(Xte)
        pred = (proba >= 0.5).astype(int)
        try:
            aucs.append(roc_auc_score(y[te], proba))
        except ValueError:
            aucs.append(float("nan"))
        f1s.append(f1_score(y[te], pred, zero_division=0))
        accs.append(accuracy_score(y[te], pred))
    return {
        "auc_mean": float(np.nanmean(aucs)),
        "auc_std":  float(np.nanstd(aucs)),
        "f1_mean":  float(np.mean(f1s)),
        "acc_mean": float(np.mean(accs)),
        "per_fold_auc": aucs,
    }


def feature_importance(X: np.ndarray, y: np.ndarray, cols: List[str]) -> pd.DataFrame:
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    clf = LogisticRegression(penalty="l1", solver="liblinear",
                             C=0.5, max_iter=2000).fit(Xs, y)
    coefs = clf.coef_.ravel()
    return pd.DataFrame({
        "feature":     cols,
        "coef":        coefs,
        "abs_coef":    np.abs(coefs),
    }).sort_values("abs_coef", ascending=False).reset_index(drop=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("[mech-clf] Building feature matrix from results/mechanistic/")
    feats = build_features()
    feats.to_csv(os.path.join(OUTPUT_DIR, "features.csv"), index=False)
    n_pairs = feats["pair_id"].nunique()
    print(f"[mech-clf] {len(feats)} rows, {n_pairs} unique pairs, "
          f"{feats.shape[1]} columns")

    X, cols = _feature_matrix(feats)
    y = _label_fragmented(feats)

    models = {
        "logistic_l2":  LogisticRegression(penalty="l2", C=1.0, max_iter=2000),
        "logistic_l1":  LogisticRegression(penalty="l1", solver="liblinear",
                                           C=0.5, max_iter=2000),
        "gbdt":         GradientBoostingClassifier(n_estimators=200, max_depth=3,
                                                   random_state=42),
    }

    rows = []
    for name, clf in models.items():
        res = stratified_cv(X, y, clf, n_splits=5)
        rows.append({
            "model":     name,
            "auc_mean":  round(res["auc_mean"], 4),
            "auc_std":   round(res["auc_std"],  4),
            "f1_mean":   round(res["f1_mean"],  4),
            "acc_mean":  round(res["acc_mean"], 4),
        })
        print(f"  {name:14s}  AUC={res['auc_mean']:.3f}±{res['auc_std']:.3f}"
              f"  F1={res['f1_mean']:.3f}  ACC={res['acc_mean']:.3f}")
    cv_df = pd.DataFrame(rows)
    cv_df.to_csv(os.path.join(OUTPUT_DIR, "cv_results.csv"), index=False)

    print("[mech-clf] Fitting L1 logistic for feature importance...")
    fi = feature_importance(X, y, cols)
    fi.to_csv(os.path.join(OUTPUT_DIR, "feature_importance.csv"), index=False)

    # Baseline: per-pair agg_mean_retrieved_mass alone (1-feature)
    one_feat_idx = cols.index("agg_mean_retrieved_mass") \
        if "agg_mean_retrieved_mass" in cols else None
    one_feat_auc = None
    if one_feat_idx is not None:
        res = stratified_cv(X[:, [one_feat_idx]], y,
                            LogisticRegression(max_iter=2000), n_splits=5)
        one_feat_auc = res["auc_mean"]
        print(f"[mech-clf] single-feature baseline "
              f"(retrieved_mass): AUC={one_feat_auc:.3f}")

    # Summary
    best = cv_df.sort_values("auc_mean", ascending=False).iloc[0]
    lines = [
        "# Mechanistic signal → coherent/fragmented classifier",
        "",
        f"- Rows: {len(feats)}  (pairs: {n_pairs}, features: {len(cols)})",
        f"- Task: predict `condition == 'fragmented'` from per-layer "
        f"attention-entropy and retrieved-mass signals.",
        "",
        "## Cross-validated performance",
        "",
        cv_df.to_markdown(index=False),
        "",
    ]
    if one_feat_auc is not None:
        lines += [
            "## Baseline",
            "",
            f"- Single-feature logistic on aggregate retrieved mass alone: "
            f"AUC = {one_feat_auc:.3f}",
            f"- Best multi-feature model: AUC = {best['auc_mean']:.3f} "
            f"(model = `{best['model']}`)",
            "",
        ]
    lines += [
        "## Top-10 L1-logistic features",
        "",
        fi.head(10).to_markdown(index=False),
        "",
        "A mean AUC ≳ 0.80 supports the claim that the coherence paradox "
        "is reflected in internal-layer activations and not just in the "
        "output-layer NLI score. The top features indicate **where** in "
        "the forward pass the fragmentation signal is most visible.",
    ]
    with open(os.path.join(OUTPUT_DIR, "summary.md"), "w") as fh:
        fh.write("\n".join(lines))
    print(f"[mech-clf] wrote -> {OUTPUT_DIR}/summary.md")


if __name__ == "__main__":
    main()
