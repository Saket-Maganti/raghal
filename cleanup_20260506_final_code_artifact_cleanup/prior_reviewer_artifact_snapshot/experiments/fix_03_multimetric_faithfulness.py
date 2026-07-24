"""
Fix 3: multi-metric faithfulness triangulation.

Consumes Fix 2 `per_query.csv` and adds:
    - faith_deberta: existing DeBERTa score
    - faith_second_nli: Vectara HEM or roberta-large-mnli proxy
    - faith_ragas: RAGAS-style LLM-as-judge score

Also creates an optional n=100 two-annotator human-eval template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from experiments.revision_utils import ensure_dirs, write_markdown_table
from src.ragas_scorer import RagasScorer
from src.vectara_hem_scorer import VectaraHEMScorer


OUT_DATA = Path("data/revision/fix_03")
OUT_RESULTS = Path("results/revision/fix_03")


def cohens_kappa(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=int)
    b = np.asarray(b, dtype=int)
    if len(a) == 0 or len(a) != len(b):
        return float("nan")
    po = float((a == b).mean())
    pa = float(a.mean())
    pb = float(b.mean())
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1.0 else float((po - pe) / (1 - pe))


def load_input(path: str, limit: int | None) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "faith_deberta" not in df.columns:
        if "faithfulness_score" in df.columns:
            df = df.rename(columns={"faithfulness_score": "faith_deberta"})
        else:
            raise ValueError("input must contain faithfulness_score or faith_deberta")
    if "context" not in df.columns:
        raise ValueError("Fix 3 requires a context column; rerun Fix 2 with current script")
    if "error" in df.columns:
        df = df[df["error"].fillna("").astype(str).eq("")].copy()
    if limit:
        df = df.head(limit).copy()
    return df


def score_metrics(args: argparse.Namespace, df: pd.DataFrame) -> pd.DataFrame:
    scorer_nli = VectaraHEMScorer(model_name=args.second_nli_model)
    scorer_ragas = RagasScorer(
        judge_backend=args.judge_backend,
        judge_model=args.judge_model,
        temperature=0.0,
    )
    if "faith_second_nli" not in df.columns:
        df["faith_second_nli"] = np.nan
        df["second_nli_label"] = ""
    if "faith_ragas" not in df.columns:
        df["faith_ragas"] = np.nan
        df["ragas_reason"] = ""

    total = len(df)
    for pos, (i, row) in enumerate(df.iterrows(), start=1):
        if not args.skip_second_nli and pd.isna(row.get("faith_second_nli")):
            try:
                out = scorer_nli.detect(row["answer"], row["context"], row.get("question", ""))
                df.at[i, "faith_second_nli"] = float(out["faithfulness_score"])
                df.at[i, "second_nli_label"] = out["label"]
            except Exception as exc:
                df.at[i, "second_nli_label"] = f"err:{type(exc).__name__}:{exc}"

        if not args.skip_ragas and pd.isna(row.get("faith_ragas")):
            try:
                out = scorer_ragas.score(
                    row["answer"],
                    row["context"],
                    question=row.get("question", ""),
                )
                df.at[i, "faith_ragas"] = float(out["faithfulness_score"])
                df.at[i, "ragas_reason"] = out["judge_reason"]
            except Exception as exc:
                df.at[i, "ragas_reason"] = f"err:{type(exc).__name__}:{exc}"

        if pos == 1 or pos % args.save_every == 0 or pos == total:
            df.to_csv(OUT_DATA / "per_query_partial.csv", index=False)
            print(f"[Fix03] scored {pos}/{total} rows")
    return df


def correlations(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["faith_deberta", "faith_second_nli", "faith_ragas"]
    rows: List[Dict[str, Any]] = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            sub = df[[a, b]].dropna()
            if len(sub) < 5:
                continue
            pr, pp = pearsonr(sub[a], sub[b])
            sr, sp = spearmanr(sub[a], sub[b])
            rows.append({
                "metric_a": a,
                "metric_b": b,
                "n": int(len(sub)),
                "pearson_r": round(float(pr), 6),
                "pearson_p": float(pp),
                "spearman_rho": round(float(sr), 6),
                "spearman_p": float(sp),
            })
    return pd.DataFrame(rows)


def condition_table(df: pd.DataFrame) -> pd.DataFrame:
    cols = {
        "deberta": ("faith_deberta", "mean"),
        "second_nli": ("faith_second_nli", "mean"),
        "ragas": ("faith_ragas", "mean"),
    }
    out = df.groupby(["dataset", "condition"]).agg(n=("question", "count"), **cols).reset_index()
    for col in ["deberta", "second_nli", "ragas"]:
        out[col] = out[col].round(6)
    return out


def build_human_template(df: pd.DataFrame, n: int, seed: int) -> None:
    rng = random.Random(seed)
    buckets = {k: list(v.index) for k, v in df.groupby("condition")}
    chosen: List[int] = []
    per = max(1, n // max(1, len(buckets)))
    for idxs in buckets.values():
        rng.shuffle(idxs)
        chosen.extend(idxs[:per])
    rng.shuffle(chosen)
    chosen = chosen[:n]
    with open(OUT_DATA / "human_eval_template.jsonl", "w") as fh:
        for idx in chosen:
            row = df.loc[idx]
            rec = {
                "id": int(idx),
                "dataset": row.get("dataset", ""),
                "condition": row.get("condition", ""),
                "question": row.get("question", ""),
                "context": str(row.get("context", ""))[:2500],
                "answer": row.get("answer", ""),
                "rater_a_faithful": "",
                "rater_b_faithful": "",
                "notes": "",
                "auto_deberta": row.get("faith_deberta", None),
                "auto_second_nli": row.get("faith_second_nli", None),
                "auto_ragas": row.get("faith_ragas", None),
            }
            fh.write(json.dumps(rec) + "\n")


def analyze_human(path: str) -> pd.DataFrame:
    rows = [json.loads(line) for line in open(path) if line.strip()]
    if not rows:
        return pd.DataFrame()
    a = np.array([int(r["rater_a_faithful"]) for r in rows])
    b = np.array([int(r["rater_b_faithful"]) for r in rows])
    majority = ((a + b) >= 1).astype(int)
    out = [{
        "n": len(rows),
        "cohens_kappa": round(cohens_kappa(a, b), 6),
        "agreement_rate": round(float((a == b).mean()), 6),
    }]
    for metric in ["auto_deberta", "auto_second_nli", "auto_ragas"]:
        vals = np.array([float(r.get(metric, np.nan)) for r in rows], dtype=float)
        mask = np.isfinite(vals)
        if mask.sum() >= 5:
            rho, p = spearmanr(majority[mask], vals[mask])
            out[0][f"spearman_{metric}"] = round(float(rho), 6)
            out[0][f"spearman_{metric}_p"] = float(p)
    return pd.DataFrame(out)


def write_columns() -> None:
    text = """# Fix 3 column documentation

`per_query.csv` extends Fix 2 rows with:

- `faith_deberta`: original DeBERTa-v3 NLI score.
- `faith_second_nli`: Vectara HEM or roberta-large-mnli score.
- `faith_ragas`: RAGAS-style LLM-as-judge faithfulness score.
- `ragas_reason`: short judge rationale.

`human_eval_template.jsonl` is an optional two-rater template. Fill
`rater_a_faithful` and `rater_b_faithful` with `0` or `1`, then rerun with
`--human_rated_path`.
"""
    (OUT_DATA / "COLUMNS.md").write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/revision/fix_02/per_query.csv")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--second_nli_model", default="roberta-large-mnli")
    parser.add_argument("--judge_backend", choices=["ollama", "together", "groq"], default="ollama")
    parser.add_argument("--judge_model", default="mistral")
    parser.add_argument("--skip_second_nli", action="store_true")
    parser.add_argument("--skip_ragas", action="store_true")
    parser.add_argument("--build_human_eval", action="store_true")
    parser.add_argument("--human_n", type=int, default=100)
    parser.add_argument("--human_rated_path", default=None)
    parser.add_argument("--save_every", type=int, default=50)
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS)
    write_columns()
    if args.human_rated_path:
        human = analyze_human(args.human_rated_path)
        human.to_csv(OUT_RESULTS / "human_eval_agreement.csv", index=False)
        print(human.to_string(index=False))
        return

    df = load_input(args.input, args.limit)
    scored = score_metrics(args, df)
    scored.to_csv(OUT_DATA / "per_query.csv", index=False)
    corr = correlations(scored)
    table = condition_table(scored)
    corr.to_csv(OUT_RESULTS / "metric_correlations.csv", index=False)
    table.to_csv(OUT_RESULTS / "table1_multimetric.csv", index=False)
    if args.build_human_eval:
        build_human_template(scored, args.human_n, seed=42)
    write_markdown_table(
        OUT_RESULTS / "summary.md",
        "Fix 3 - multi-metric faithfulness",
        {"Condition Means": table, "Metric Correlations": corr},
    )
    print(f"[Fix03] wrote {len(scored)} scored rows")


if __name__ == "__main__":
    main()
