"""
Fix 12: answer-span/control diagnostic for the matched-CCS cell.

This script uses the Fix 1 matched HIGH/LOW CCS contexts and asks whether
answer-bearing evidence presence explains faithfulness/hallucination better
than CCS, mean query similarity, or simple combinations of those variables.

It does not call any paid API.  The span detector is deliberately lexical and
traceable: lowercase, strip punctuation, collapse whitespace, then test whether
any normalized gold-answer alias appears in the normalized retrieved context.

Primary command:

    python3 experiments/fix_12_answer_span_diagnostic.py

Outputs:
    data/revision/fix_12/span_control_rows.csv
    results/revision/fix_12/span_control_summary.csv
    results/revision/fix_12/span_control_models.csv
    results/revision/fix_12/span_control_report.md
    source_tables/span_control_summary.csv
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import string
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from experiments.revision_utils import ensure_dirs


OUT_DATA = Path("data/revision/fix_12")
OUT_RESULTS = Path("results/revision/fix_12")
OUT_SOURCE = Path("source_tables")
DEFAULT_PER_QUERY = Path("data/revision/fix_01/per_query.csv")
DEFAULT_MATCHED = Path("data/revision/fix_01/matched_pairs.csv")
N_BOOTSTRAP = 10_000


PUNCT_TABLE = str.maketrans({ch: " " for ch in string.punctuation})


def normalize_text(text: Any) -> str:
    text = "" if text is None or (isinstance(text, float) and math.isnan(text)) else str(text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().translate(PUNCT_TABLE)
    return re.sub(r"\s+", " ", text).strip()


def answer_aliases(answer: Any) -> List[str]:
    raw = "" if answer is None or (isinstance(answer, float) and math.isnan(answer)) else str(answer)
    aliases: List[str] = []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            aliases.extend(str(x) for x in parsed)
        elif isinstance(parsed, dict):
            for key in ("text", "answer", "answers", "aliases"):
                val = parsed.get(key)
                if isinstance(val, list):
                    aliases.extend(str(x) for x in val)
                elif val:
                    aliases.append(str(val))
    except Exception:
        pass

    aliases.append(raw)
    # Common low-risk separators in QA exports; keep this conservative.
    for sep in ["||", ";", " / "]:
        if sep in raw:
            aliases.extend(part for part in raw.split(sep))

    cleaned: List[str] = []
    seen = set()
    for alias in aliases:
        norm = normalize_text(alias)
        if norm and norm not in seen:
            cleaned.append(norm)
            seen.add(norm)
    return cleaned


def span_present(answer: Any, context: Any) -> bool:
    norm_context = normalize_text(context)
    return any(alias in norm_context for alias in answer_aliases(answer))


def parse_passages(value: Any) -> List[str]:
    if pd.isna(value):
        return []
    try:
        parsed = json.loads(str(value))
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except Exception:
        return []
    return []


def truthy_series(values: pd.Series) -> pd.Series:
    return values.astype(str).str.lower().isin(["true", "1", "yes", "y"])


def build_rows(per_query_path: Path, matched_path: Path) -> pd.DataFrame:
    per_query = pd.read_csv(per_query_path)
    matched = pd.read_csv(matched_path)
    context_rows: List[Dict[str, Any]] = []
    for _, row in matched.iterrows():
        for set_type, passage_col in [
            ("high_ccs", "high_passages_json"),
            ("low_ccs", "low_passages_json"),
        ]:
            passages = parse_passages(row[passage_col])
            context_rows.append(
                {
                    "pair_id": row["pair_id"],
                    "set_type": set_type,
                    "context": "\n\n".join(passages),
                    "n_passages": len(passages),
                }
            )
    contexts = pd.DataFrame(context_rows)
    df = per_query.merge(contexts, on=["pair_id", "set_type"], how="left")
    df = df[df.get("error", "").fillna("").astype(str).eq("")].copy()
    df["answer_span_present"] = [
        span_present(ans, ctx) for ans, ctx in zip(df["ground_truth"], df["context"])
    ]
    df["hallucination_label"] = truthy_series(df["is_hallucination"]).astype(int)
    df["answer_span_present_int"] = df["answer_span_present"].astype(int)
    for col in ["faithfulness_score", "mean_query_sim", "ccs"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


MODEL_SPECS: List[tuple[str, List[str]]] = [
    ("answer_span_present", ["answer_span_present_int"]),
    ("mean_query_similarity", ["mean_query_sim"]),
    ("ccs", ["ccs"]),
    ("answer_span_present + mean_query_similarity", ["answer_span_present_int", "mean_query_sim"]),
    ("answer_span_present + ccs", ["answer_span_present_int", "ccs"]),
    (
        "answer_span_present + mean_query_similarity + ccs",
        ["answer_span_present_int", "mean_query_sim", "ccs"],
    ),
]


def adjusted_r2(r2: float, n: int, p: int) -> float:
    if n <= p + 1:
        return float("nan")
    return 1.0 - (1.0 - r2) * (n - 1) / (n - p - 1)


def fit_linear(df: pd.DataFrame, predictors: Sequence[str]) -> Dict[str, Any]:
    sub = df[list(predictors) + ["faithfulness_score"]].dropna()
    x = sub[list(predictors)].to_numpy(dtype=float)
    y = sub["faithfulness_score"].to_numpy(dtype=float)
    model = LinearRegression().fit(x, y)
    pred = model.predict(x)
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    coefs = {name: float(value) for name, value in zip(predictors, model.coef_)}
    return {
        "n": int(len(sub)),
        "r2": r2,
        "adjusted_r2": adjusted_r2(r2, len(sub), len(predictors)),
        "coefficients_json": json.dumps(coefs, sort_keys=True),
        "intercept": float(model.intercept_),
    }


def fit_logistic(df: pd.DataFrame, predictors: Sequence[str]) -> Dict[str, Any]:
    sub = df[list(predictors) + ["hallucination_label"]].dropna()
    x_raw = sub[list(predictors)].to_numpy(dtype=float)
    y = sub["hallucination_label"].to_numpy(dtype=int)
    if len(np.unique(y)) < 2:
        return {
            "n": int(len(sub)),
            "auroc": float("nan"),
            "aic": float("nan"),
            "coefficients_json": "{}",
            "intercept": float("nan"),
        }
    scaler = StandardScaler()
    x = scaler.fit_transform(x_raw)
    model = LogisticRegression(C=1_000_000.0, max_iter=500, solver="lbfgs").fit(x, y)
    probs = np.clip(model.predict_proba(x)[:, 1], 1e-9, 1 - 1e-9)
    ll = float(np.sum(y * np.log(probs) + (1 - y) * np.log(1 - probs)))
    k = len(predictors) + 1
    aic = 2 * k - 2 * ll
    # Report standardized coefficients for continuous comparability.
    coefs = {name: float(value) for name, value in zip(predictors, model.coef_[0])}
    return {
        "n": int(len(sub)),
        "auroc": float(roc_auc_score(y, probs)),
        "aic": aic,
        "coefficients_json": json.dumps(coefs, sort_keys=True),
        "intercept": float(model.intercept_[0]),
    }


def bootstrap_metric(
    df: pd.DataFrame,
    predictors: Sequence[str],
    kind: str,
    metric_name: str,
    seed: int,
    n_resamples: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    vals: List[float] = []
    n = len(df)
    for _ in range(n_resamples):
        sample = df.iloc[rng.integers(0, n, size=n)]
        try:
            if kind == "linear":
                value = fit_linear(sample, predictors)[metric_name]
            else:
                value = fit_logistic(sample, predictors)[metric_name]
        except Exception:
            value = float("nan")
        if np.isfinite(value):
            vals.append(float(value))
    if not vals:
        return float("nan"), float("nan")
    return float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))


def model_table(df: pd.DataFrame, n_bootstrap: int) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for name, predictors in MODEL_SPECS:
        lin = fit_linear(df, predictors)
        r2_lo, r2_hi = bootstrap_metric(df, predictors, "linear", "r2", 42, n_bootstrap)
        rows.append(
            {
                "outcome": "faithfulness_score",
                "model": name,
                "predictors": "+".join(predictors),
                "n": lin["n"],
                "metric": "r2",
                "value": round(lin["r2"], 6),
                "ci95_lo": round(r2_lo, 6),
                "ci95_hi": round(r2_hi, 6),
                "secondary_metric": "adjusted_r2",
                "secondary_value": round(lin["adjusted_r2"], 6),
                "aic": "",
                "coefficients_json": lin["coefficients_json"],
            }
        )

        logit = fit_logistic(df, predictors)
        auc_lo, auc_hi = bootstrap_metric(df, predictors, "logistic", "auroc", 43, n_bootstrap)
        rows.append(
            {
                "outcome": "hallucination_label",
                "model": name,
                "predictors": "+".join(predictors),
                "n": logit["n"],
                "metric": "auroc",
                "value": round(logit["auroc"], 6),
                "ci95_lo": round(auc_lo, 6),
                "ci95_hi": round(auc_hi, 6),
                "secondary_metric": "",
                "secondary_value": "",
                "aic": round(logit["aic"], 6) if np.isfinite(logit["aic"]) else "",
                "coefficients_json": logit["coefficients_json"],
            }
        )
    return pd.DataFrame(rows)


def summary_table(df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for name, sub in [("all", df), *list(df.groupby("set_type"))]:
        rows.append(
            {
                "group": name,
                "n": int(len(sub)),
                "answer_span_present_rate": round(float(sub["answer_span_present"].mean()), 6),
                "faithfulness_mean": round(float(sub["faithfulness_score"].mean()), 6),
                "hallucination_rate": round(float(sub["hallucination_label"].mean()), 6),
                "mean_query_similarity": round(float(sub["mean_query_sim"].mean()), 6),
                "ccs_mean": round(float(sub["ccs"].mean()), 6),
            }
        )
    for present, sub in df.groupby("answer_span_present"):
        rows.append(
            {
                "group": f"span_present={bool(present)}",
                "n": int(len(sub)),
                "answer_span_present_rate": round(float(sub["answer_span_present"].mean()), 6),
                "faithfulness_mean": round(float(sub["faithfulness_score"].mean()), 6),
                "hallucination_rate": round(float(sub["hallucination_label"].mean()), 6),
                "mean_query_similarity": round(float(sub["mean_query_sim"].mean()), 6),
                "ccs_mean": round(float(sub["ccs"].mean()), 6),
            }
        )
    return pd.DataFrame(rows)


def write_report(summary: pd.DataFrame, models: pd.DataFrame, out_path: Path) -> None:
    faith_rank = models[models["outcome"].eq("faithfulness_score")].sort_values("value", ascending=False)
    halluc_rank = models[models["outcome"].eq("hallucination_label")].sort_values("value", ascending=False)
    best_faith = faith_rank.iloc[0]
    best_halluc = halluc_rank.iloc[0]
    span_only = models[models["model"].eq("answer_span_present")]
    lines = [
        "# Fix 12 - answer-span/control diagnostic",
        "",
        "Source: `data/revision/fix_01/{matched_pairs.csv,per_query.csv}`.",
        "No model calls or paid APIs are used.",
        "",
        "## Span and outcome summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Model comparison",
        "",
        models.to_markdown(index=False),
        "",
        "## Compact interpretation",
        "",
        (
            f"The highest faithfulness R^2 model is `{best_faith['model']}` "
            f"(R^2={best_faith['value']})."
        ),
        (
            f"The highest hallucination AUROC model is `{best_halluc['model']}` "
            f"(AUROC={best_halluc['value']})."
        ),
        "This is a matched SQuAD/Mistral diagnostic only; it does not establish a universal mechanism.",
        "",
        "## Span-only reference",
        "",
        span_only.to_markdown(index=False),
        "",
    ]
    out_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per_query", default=str(DEFAULT_PER_QUERY))
    parser.add_argument("--matched_pairs", default=str(DEFAULT_MATCHED))
    parser.add_argument("--n_bootstrap", type=int, default=N_BOOTSTRAP)
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS, OUT_SOURCE)
    df = build_rows(Path(args.per_query), Path(args.matched_pairs))
    df.to_csv(OUT_DATA / "span_control_rows.csv", index=False)

    summary = summary_table(df)
    models = model_table(df, n_bootstrap=args.n_bootstrap)
    summary.to_csv(OUT_RESULTS / "span_control_summary.csv", index=False)
    models.to_csv(OUT_RESULTS / "span_control_models.csv", index=False)

    source = models[
        [
            "outcome",
            "model",
            "n",
            "metric",
            "value",
            "ci95_lo",
            "ci95_hi",
            "secondary_metric",
            "secondary_value",
            "aic",
        ]
    ].copy()
    source.to_csv(OUT_SOURCE / "span_control_summary.csv", index=False)
    write_report(summary, models, OUT_RESULTS / "span_control_report.md")

    print(f"[Fix12] wrote {len(df)} context rows")
    print(models[["outcome", "model", "metric", "value", "ci95_lo", "ci95_hi"]].to_string(index=False))


if __name__ == "__main__":
    main()
