"""
Fix 14: compact second-generator metric-fragility replication.

The main 7,500-row metric-fragility cell uses Mistral fixed generations.
This script reuses the same fixed retrieved contexts from Fix 2, generates
answers with a second local Ollama generator (default: Qwen2.5-7B), and scores
the fixed generations with DeBERTa, a second NLI model, and a local
RAGAS-style judge.

No paid APIs are used. If local runtime is too slow, use an equivalent GPU
environment with the same command.

Primary local command:

    python3 experiments/fix_14_second_generator_metric_fragility.py \\
        --n_per_condition 100 --generator_model qwen2.5

Smoke command:

    python3 experiments/fix_14_second_generator_metric_fragility.py \\
        --n_per_condition 5 --generator_model qwen2.5 --skip_ragas

Outputs when completed:
    data/revision/fix_14/second_generator_per_query.csv
    results/revision/fix_14/second_generator_metrics.csv
    results/revision/fix_14/second_generator_correlations.csv
    results/revision/fix_14/second_generator_report.md
    source_tables/second_generator_metrics.csv
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from experiments.revision_utils import ensure_dirs
from src.hallucination_detector import HallucinationDetector
from src.ragas_scorer import RagasScorer
from src.rag_pipeline import RAG_PROMPT
from src.vectara_hem_scorer import VectaraHEMScorer


OUT_DATA = Path("data/revision/fix_14")
OUT_RESULTS = Path("results/revision/fix_14")
OUT_SOURCE = Path("source_tables")
CONDITIONS = ["baseline", "hcpc_v1", "hcpc_v2"]


def load_sample(path: Path, n_per_condition: int, seed: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"question", "ground_truth", "condition", "context", "dataset"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"input missing required columns: {sorted(missing)}")
    df = df[df["condition"].isin(CONDITIONS)].copy()
    parts: List[pd.DataFrame] = []
    for condition in CONDITIONS:
        sub = df[df["condition"].eq(condition)].copy()
        if len(sub) > n_per_condition:
            sub = sub.sample(n=n_per_condition, random_state=seed)
        parts.append(sub)
    out = pd.concat(parts, ignore_index=False).sort_index().reset_index().rename(columns={"index": "source_row"})
    return out


def read_existing(path: Path) -> pd.DataFrame:
    if path.exists() and path.stat().st_size:
        return pd.read_csv(path)
    return pd.DataFrame()


def make_llm(model: str, temperature: float):
    from langchain_ollama import OllamaLLM

    base_url = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST")
    kwargs: Dict[str, Any] = {"model": model, "temperature": temperature}
    if base_url:
        if not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"
        kwargs["base_url"] = base_url
    return OllamaLLM(**kwargs)


def generate_answers(sample: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    out_path = OUT_DATA / "second_generator_per_query.csv"
    existing = read_existing(out_path)
    done = set()
    if not existing.empty:
        done = set(existing["row_id"].astype(str))

    llm = make_llm(args.generator_model, args.temperature)
    rows = existing.to_dict("records") if not existing.empty else []
    total = len(sample)
    for pos, row in sample.iterrows():
        row_id = f"{int(row['source_row'])}:{row['condition']}:{args.generator_model}"
        if row_id in done:
            continue
        prompt = RAG_PROMPT.format(context=str(row["context"])[: args.context_chars], question=row["question"])
        start = time.time()
        try:
            answer = llm.invoke(prompt)
            error = ""
        except Exception as exc:
            answer = ""
            error = f"{type(exc).__name__}: {exc}"
        rec = {
            "row_id": row_id,
            "source_row": int(row["source_row"]),
            "dataset": row.get("dataset", ""),
            "seed": row.get("seed", ""),
            "condition": row["condition"],
            "question": row["question"],
            "ground_truth": row.get("ground_truth", ""),
            "context": row["context"],
            "mean_retrieval_similarity": row.get("mean_retrieval_similarity", np.nan),
            "ccs": row.get("ccs", np.nan),
            "refined": row.get("refined", ""),
            "generator_model": args.generator_model,
            "answer": answer,
            "generation_latency_s": round(time.time() - start, 4),
            "error": error,
            "faith_deberta": np.nan,
            "is_hallucination": "",
            "faith_second_nli": np.nan,
            "second_nli_label": "",
            "faith_ragas": np.nan,
            "ragas_reason": "",
        }
        rows.append(rec)
        if len(rows) == 1 or len(rows) % args.save_every == 0:
            pd.DataFrame(rows).to_csv(out_path, index=False)
            print(f"[Fix14] generated/scaffolded {len(rows)}/{total}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    return df


def score_rows(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    out_path = OUT_DATA / "second_generator_per_query.csv"
    ok = df["error"].fillna("").astype(str).eq("")

    detector = None if args.skip_deberta else HallucinationDetector()
    second = None if args.skip_second_nli else VectaraHEMScorer(model_name=args.second_nli_model)
    ragas = None if args.skip_ragas else RagasScorer(judge_backend="ollama", judge_model=args.ragas_judge_model)

    total = int(ok.sum())
    seen = 0
    for idx, row in df[ok].iterrows():
        seen += 1
        answer = str(row.get("answer", ""))
        context = str(row.get("context", ""))
        question = str(row.get("question", ""))

        if detector is not None and pd.isna(row.get("faith_deberta")):
            try:
                out = detector.detect(answer, context)
                df.at[idx, "faith_deberta"] = float(out["faithfulness_score"])
                df.at[idx, "is_hallucination"] = bool(out["is_hallucination"])
            except Exception as exc:
                df.at[idx, "is_hallucination"] = f"err:{type(exc).__name__}:{exc}"

        if second is not None and pd.isna(row.get("faith_second_nli")):
            try:
                out = second.detect(answer, context, question=question)
                df.at[idx, "faith_second_nli"] = float(out["faithfulness_score"])
                df.at[idx, "second_nli_label"] = out["label"]
            except Exception as exc:
                df.at[idx, "second_nli_label"] = f"err:{type(exc).__name__}:{exc}"

        if ragas is not None and pd.isna(row.get("faith_ragas")):
            try:
                out = ragas.score(answer, context, question=question)
                df.at[idx, "faith_ragas"] = float(out["faithfulness_score"])
                df.at[idx, "ragas_reason"] = out["judge_reason"]
            except Exception as exc:
                df.at[idx, "ragas_reason"] = f"err:{type(exc).__name__}:{exc}"

        if seen == 1 or seen % args.save_every == 0 or seen == total:
            df.to_csv(out_path, index=False)
            print(f"[Fix14] scored {seen}/{total}", flush=True)
    df.to_csv(out_path, index=False)
    return df


def metric_table(df: pd.DataFrame) -> pd.DataFrame:
    metrics = ["faith_deberta", "faith_second_nli", "faith_ragas"]
    rows: List[Dict[str, Any]] = []
    ok = df[df["error"].fillna("").astype(str).eq("")].copy()
    for metric in metrics:
        valid = ok.dropna(subset=[metric])
        if valid.empty:
            continue
        means = valid.groupby("condition")[metric].mean()
        counts = valid.groupby("condition")[metric].count()
        rows.append(
            {
                "generator_model": valid["generator_model"].iloc[0],
                "metric": metric,
                "n_baseline": int(counts.get("baseline", 0)),
                "n_hcpc_v1": int(counts.get("hcpc_v1", 0)),
                "n_hcpc_v2": int(counts.get("hcpc_v2", 0)),
                "faith_baseline": round(float(means.get("baseline", np.nan)), 6),
                "faith_hcpc_v1": round(float(means.get("hcpc_v1", np.nan)), 6),
                "faith_hcpc_v2": round(float(means.get("hcpc_v2", np.nan)), 6),
                "paradox_drop_baseline_minus_v1": round(
                    float(means.get("baseline", np.nan) - means.get("hcpc_v1", np.nan)), 6
                ),
                "v2_recovery_v2_minus_v1": round(
                    float(means.get("hcpc_v2", np.nan) - means.get("hcpc_v1", np.nan)), 6
                ),
            }
        )
    return pd.DataFrame(rows)


def correlations(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["faith_deberta", "faith_second_nli", "faith_ragas"]
    rows: List[Dict[str, Any]] = []
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            sub = df[[a, b]].dropna()
            if len(sub) < 5:
                continue
            pr, pp = pearsonr(sub[a], sub[b])
            sr, sp = spearmanr(sub[a], sub[b])
            rows.append(
                {
                    "metric_a": a,
                    "metric_b": b,
                    "n": int(len(sub)),
                    "pearson_r": round(float(pr), 6),
                    "pearson_p": float(pp),
                    "spearman_rho": round(float(sr), 6),
                    "spearman_p": float(sp),
                }
            )
    return pd.DataFrame(rows)


def write_report(metrics: pd.DataFrame, corr: pd.DataFrame, args: argparse.Namespace) -> None:
    lines = [
        "# Fix 14 - second-generator metric-fragility replication",
        "",
        f"Generator: `{args.generator_model}` via local Ollama. Sample target: {args.n_per_condition} rows per condition.",
        "No paid APIs are used.",
        "",
        "## Metric means and effect sizes",
        "",
        metrics.to_markdown(index=False) if not metrics.empty else "(no completed metric rows)",
        "",
        "## Metric correlations",
        "",
        corr.to_markdown(index=False) if not corr.empty else "(not enough completed metric overlap)",
        "",
        "## Compact interpretation",
        "",
        "If scorer disagreement persists here, it reduces the concern that the main metric-fragility result is purely Mistral-specific.",
        "If it does not persist, generator identity should be treated as another required audit axis.",
        "",
    ]
    (OUT_RESULTS / "second_generator_report.md").write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/revision/fix_02/per_query.csv")
    parser.add_argument("--n_per_condition", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--generator_model", default="qwen2.5")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--context_chars", type=int, default=4500)
    parser.add_argument("--second_nli_model", default="roberta-large-mnli")
    parser.add_argument("--ragas_judge_model", default="mistral")
    parser.add_argument("--skip_generation", action="store_true")
    parser.add_argument("--skip_deberta", action="store_true")
    parser.add_argument("--skip_second_nli", action="store_true")
    parser.add_argument("--skip_ragas", action="store_true")
    parser.add_argument("--save_every", type=int, default=10)
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS, OUT_SOURCE)
    sample = load_sample(Path(args.input), args.n_per_condition, args.seed)
    sample.to_csv(OUT_DATA / "second_generator_sample_manifest.csv", index=False)

    if args.skip_generation and (OUT_DATA / "second_generator_per_query.csv").exists():
        df = pd.read_csv(OUT_DATA / "second_generator_per_query.csv")
    else:
        df = generate_answers(sample, args)
    df = score_rows(df, args)

    metrics = metric_table(df)
    corr = correlations(df)
    metrics.to_csv(OUT_RESULTS / "second_generator_metrics.csv", index=False)
    corr.to_csv(OUT_RESULTS / "second_generator_correlations.csv", index=False)
    metrics.to_csv(OUT_SOURCE / "second_generator_metrics.csv", index=False)
    write_report(metrics, corr, args)
    print(metrics.to_string(index=False))
    if not corr.empty:
        print(corr.to_string(index=False))


if __name__ == "__main__":
    main()
