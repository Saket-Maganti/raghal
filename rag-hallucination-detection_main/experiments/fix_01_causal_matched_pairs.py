"""
Fix 1: causal coherence intervention via matched-similarity triples.

This is the highest-priority NeurIPS revision experiment.  For each SQuAD
query, the script retrieves the top-20 passages, enumerates every 3-passage
triple, and finds a HIGH-CCS and LOW-CCS triple with matched mean query
similarity (<= 0.02 absolute gap).  Generation and NLI scoring can be run in
the same pass or later from the saved matched-pair CSV.

Primary preregistered command:

    python3 experiments/fix_01_causal_matched_pairs.py \\
        --stage full --dataset squad --n_target 200 --seed 42 \\
        --max_contexts 400 --candidate_limit 400 \\
        --backend ollama --model mistral

Cheap construction smoke test:

    python3 experiments/fix_01_causal_matched_pairs.py \\
        --stage construct --dataset squad --n_target 10 \\
        --max_contexts 80 --candidate_limit 40

Outputs:
    data/revision/fix_01/matched_pairs.csv
    data/revision/fix_01/per_query.csv
    data/revision/fix_01/skipped_queries.csv
    data/revision/fix_01/COLUMNS.md
    results/revision/fix_01/*.csv
    results/revision/fix_01/summary.md
    ragpaper/figures/fix_01_paired_diff.pdf
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.hallucination_detector import HallucinationDetector
from src.rag_pipeline import RAGPipeline, RAG_PROMPT


OUT_DATA = Path("data/revision/fix_01")
OUT_RESULTS = Path("results/revision/fix_01")
OUT_FIG = Path("ragpaper/figures/fix_01_paired_diff.pdf")

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_N = 20
TRIPLE_K = 3
SIM_TOL = 0.02
SIM_BUCKET = 0.02
CCS_GAP_MIN = 0.05
MAX_OVERLAP = 1
N_BOOTSTRAP = 10_000
SKIPPED_COLUMNS = ["dataset", "query_index", "question", "reason", "n_candidates"]
PER_QUERY_COLUMNS = [
    "pair_id", "dataset", "query_index", "question", "ground_truth", "model",
    "backend", "seed", "set_type", "passage_idxs", "mean_query_sim", "ccs",
    "sim_gap", "ccs_gap", "overlap", "answer", "faithfulness_score",
    "is_hallucination", "nli_label", "latency_s", "error",
]
PAIRED_COLUMNS = [
    "dataset", "n_pairs", "mean_faith_high", "mean_faith_low",
    "mean_diff_high_minus_low", "wilcoxon_stat", "wilcoxon_p_greater",
    "cohens_dz", "boot_ci95_lo", "boot_ci95_hi",
    "hallucination_rate_high", "hallucination_rate_low",
    "matched_odds_ratio_low_vs_high", "discordant_low_only",
    "discordant_high_only", "mean_similarity_delta_high_minus_low",
    "max_abs_similarity_delta", "similarity_wilcoxon_stat",
    "similarity_wilcoxon_p_two_sided", "h1_supported",
]
BOOT_COLUMNS = [
    "dataset", "n_pairs", "n_resamples", "statistic", "estimate",
    "ci95_lo", "ci95_hi",
]


@dataclass(frozen=True)
class TripleRecord:
    idxs: Tuple[int, int, int]
    mean_query_sim: float
    ccs: float
    bucket_id: int


@dataclass(frozen=True)
class MatchedPair:
    pair_id: str
    dataset: str
    query_index: int
    question: str
    ground_truth: str
    seed: int
    n_candidates: int
    n_triples_evaluated: int
    bucket_id: int
    bucket_size: int
    high_idxs: str
    low_idxs: str
    high_passages_json: str
    low_passages_json: str
    mean_sim_high: float
    mean_sim_low: float
    sim_gap: float
    ccs_high: float
    ccs_low: float
    ccs_gap: float
    overlap: int
    top20_mean_query_sim: float
    top20_min_query_sim: float
    top20_max_query_sim: float
    construction_version: str = "fix01_matched_triples_v2"


def _stable_id(text: str, prefix: str = "") -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}{digest}" if prefix else digest


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(norms, 1e-12)


def _ccs_from_unit_embeddings(unit_embeddings: np.ndarray,
                              idxs: Sequence[int]) -> float:
    sub = unit_embeddings[list(idxs)]
    sims = sub @ sub.T
    upper = sims[np.triu_indices(len(sub), k=1)]
    if upper.size == 0:
        return 1.0
    return float(upper.mean() - upper.std())


def _bucket_id(mean_query_sim: float, bucket_width: float) -> int:
    # Shift by +1.0 so negative cosine values have stable bucket boundaries.
    return int(np.floor((mean_query_sim + 1.0) / bucket_width))


def enumerate_triples(query_emb: np.ndarray,
                      passage_embs: np.ndarray,
                      sim_bucket: float = SIM_BUCKET) -> Tuple[List[TripleRecord], np.ndarray]:
    q = query_emb / max(float(np.linalg.norm(query_emb)), 1e-12)
    p = _l2_normalize(passage_embs)
    query_sims = p @ q

    records: List[TripleRecord] = []
    for idxs in combinations(range(len(passage_embs)), TRIPLE_K):
        mean_sim = float(query_sims[list(idxs)].mean())
        ccs = _ccs_from_unit_embeddings(p, idxs)
        records.append(
            TripleRecord(
                idxs=tuple(int(i) for i in idxs),
                mean_query_sim=mean_sim,
                ccs=ccs,
                bucket_id=_bucket_id(mean_sim, sim_bucket),
            )
        )
    return records, query_sims


def find_matched_pair(query_emb: np.ndarray,
                      passage_embs: np.ndarray,
                      sim_tol: float = SIM_TOL,
                      sim_bucket: float = SIM_BUCKET,
                      ccs_gap_min: float = CCS_GAP_MIN,
                      max_overlap: int = MAX_OVERLAP) -> Optional[Dict[str, Any]]:
    """Return the highest-gap HIGH/LOW CCS pair at matched query similarity."""
    if len(passage_embs) < TOP_N:
        return None

    records, query_sims = enumerate_triples(query_emb, passage_embs, sim_bucket)
    buckets: Dict[int, List[TripleRecord]] = {}
    for rec in records:
        buckets.setdefault(rec.bucket_id, []).append(rec)

    best: Optional[Dict[str, Any]] = None
    best_key: Optional[Tuple[float, float, int]] = None

    for bucket, members in buckets.items():
        if len(members) < 4:
            continue
        ordered = sorted(members, key=lambda r: r.ccs)

        for low in ordered:
            for high in reversed(ordered):
                ccs_gap = high.ccs - low.ccs
                if ccs_gap < ccs_gap_min:
                    break
                sim_gap = abs(high.mean_query_sim - low.mean_query_sim)
                if sim_gap > sim_tol:
                    continue
                overlap = len(set(high.idxs) & set(low.idxs))
                if overlap > max_overlap:
                    continue

                candidate_key = (ccs_gap, -sim_gap, -overlap)
                if best_key is None or candidate_key > best_key:
                    best_key = candidate_key
                    best = {
                        "bucket_id": bucket,
                        "bucket_size": len(members),
                        "idxs_high": high.idxs,
                        "idxs_low": low.idxs,
                        "mean_sim_high": high.mean_query_sim,
                        "mean_sim_low": low.mean_query_sim,
                        "ccs_high": high.ccs,
                        "ccs_low": low.ccs,
                        "sim_gap": sim_gap,
                        "ccs_gap": ccs_gap,
                        "overlap": overlap,
                        "n_triples_evaluated": len(records),
                        "top20_mean_query_sim": float(query_sims.mean()),
                        "top20_min_query_sim": float(query_sims.min()),
                        "top20_max_query_sim": float(query_sims.max()),
                    }
    return best


def _ensure_dirs() -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_RESULTS.mkdir(parents=True, exist_ok=True)
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _collection_name(dataset: str, seed: int, max_contexts: int, run_tag: str) -> str:
    safe_tag = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in run_tag)
    return f"fix01_{dataset}_seed{seed}_ctx{max_contexts}_{safe_tag}"[:63]


def _build_pipeline(dataset: str,
                    seed: int,
                    max_contexts: int,
                    run_tag: str,
                    persist_dir: str) -> Tuple[RAGPipeline, List[dict]]:
    docs, qa = load_dataset_by_name(dataset, max_papers=max_contexts)
    if not docs or not qa:
        raise RuntimeError(f"{dataset}: loader returned no documents or QA pairs")

    pipe = RAGPipeline(
        chunk_size=1024,
        chunk_overlap=100,
        top_k=TOP_N,
        model_name="mistral",
        embed_model=EMBED_MODEL,
        persist_dir=persist_dir,
    )
    pipe.index_documents(
        docs,
        collection_name=_collection_name(dataset, seed, max_contexts, run_tag),
    )
    return pipe, qa


def construct_pairs(args: argparse.Namespace) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if args.dataset not in DATASET_REGISTRY:
        raise ValueError(f"Unknown dataset {args.dataset!r}")

    rows: List[MatchedPair] = []
    skipped: List[Dict[str, Any]] = []
    rng = random.Random(args.seed)
    run_tag = args.run_tag or time.strftime("%Y%m%d_%H%M%S")

    def _construct_with_persist(persist_dir: str) -> None:
        pipe, qa_pairs = _build_pipeline(
            dataset=args.dataset,
            seed=args.seed,
            max_contexts=args.max_contexts,
            run_tag=run_tag,
            persist_dir=persist_dir,
        )
        shuffled = list(enumerate(qa_pairs))
        rng.shuffle(shuffled)
        candidates = shuffled[:args.candidate_limit]

        print(
            f"[Fix01/construct] dataset={args.dataset} "
            f"target={args.n_target} candidates={len(candidates)} "
            f"max_contexts={args.max_contexts}",
            flush=True,
        )
        t0 = time.time()
        for attempt, (query_index, qa) in enumerate(candidates, start=1):
            if len(rows) >= args.n_target:
                break
            question = qa["question"]
            try:
                docs, _scores = pipe.retrieve_with_scores(question)
            except Exception as exc:
                skipped.append({
                    "dataset": args.dataset,
                    "query_index": query_index,
                    "question": question,
                    "reason": f"retrieve_error:{type(exc).__name__}:{exc}",
                })
                continue

            if len(docs) < TOP_N:
                skipped.append({
                    "dataset": args.dataset,
                    "query_index": query_index,
                    "question": question,
                    "reason": "fewer_than_top20_candidates",
                    "n_candidates": len(docs),
                })
                continue

            texts = [d.page_content for d in docs[:TOP_N]]
            try:
                passage_embs = np.asarray(
                    pipe.embeddings.embed_documents(texts),
                    dtype=np.float64,
                )
                query_emb = np.asarray(
                    pipe.embeddings.embed_query(question),
                    dtype=np.float64,
                )
            except Exception as exc:
                skipped.append({
                    "dataset": args.dataset,
                    "query_index": query_index,
                    "question": question,
                    "reason": f"embedding_error:{type(exc).__name__}:{exc}",
                    "n_candidates": len(docs),
                })
                continue

            pair = find_matched_pair(query_emb, passage_embs)
            if pair is None:
                skipped.append({
                    "dataset": args.dataset,
                    "query_index": query_index,
                    "question": question,
                    "reason": "no_matched_pair",
                    "n_candidates": len(docs),
                })
                continue

            high_texts = [texts[i] for i in pair["idxs_high"]]
            low_texts = [texts[i] for i in pair["idxs_low"]]
            pair_id = _stable_id(f"{args.dataset}:{query_index}:{question}", "fix01_")
            rows.append(
                MatchedPair(
                    pair_id=pair_id,
                    dataset=args.dataset,
                    query_index=int(query_index),
                    question=question,
                    ground_truth=qa.get("ground_truth", ""),
                    seed=int(args.seed),
                    n_candidates=int(len(docs)),
                    n_triples_evaluated=int(pair["n_triples_evaluated"]),
                    bucket_id=int(pair["bucket_id"]),
                    bucket_size=int(pair["bucket_size"]),
                    high_idxs=json.dumps(list(pair["idxs_high"])),
                    low_idxs=json.dumps(list(pair["idxs_low"])),
                    high_passages_json=json.dumps(high_texts),
                    low_passages_json=json.dumps(low_texts),
                    mean_sim_high=round(float(pair["mean_sim_high"]), 6),
                    mean_sim_low=round(float(pair["mean_sim_low"]), 6),
                    sim_gap=round(float(pair["sim_gap"]), 6),
                    ccs_high=round(float(pair["ccs_high"]), 6),
                    ccs_low=round(float(pair["ccs_low"]), 6),
                    ccs_gap=round(float(pair["ccs_gap"]), 6),
                    overlap=int(pair["overlap"]),
                    top20_mean_query_sim=round(float(pair["top20_mean_query_sim"]), 6),
                    top20_min_query_sim=round(float(pair["top20_min_query_sim"]), 6),
                    top20_max_query_sim=round(float(pair["top20_max_query_sim"]), 6),
                )
            )

            if len(rows) <= 3 or len(rows) % args.progress_every == 0:
                elapsed = time.time() - t0
                print(
                    f"[Fix01/construct] pairs={len(rows)}/{args.n_target} "
                    f"attempts={attempt} skipped={len(skipped)} "
                    f"elapsed={elapsed:.1f}s",
                    flush=True,
                )

    if args.persist_dir:
        Path(args.persist_dir).mkdir(parents=True, exist_ok=True)
        _construct_with_persist(args.persist_dir)
    else:
        with tempfile.TemporaryDirectory(prefix=f"fix01_{args.dataset}_") as tmp:
            _construct_with_persist(tmp)

    pairs_df = pd.DataFrame([asdict(r) for r in rows])
    skipped_df = pd.DataFrame(skipped, columns=SKIPPED_COLUMNS)
    _ensure_dirs()
    pairs_df.to_csv(OUT_DATA / "matched_pairs.csv", index=False)
    skipped_df.to_csv(OUT_DATA / "skipped_queries.csv", index=False)
    write_columns_doc()
    write_construct_only_per_query(pairs_df)
    per_query_path = OUT_DATA / "per_query.csv"
    if not per_query_path.exists():
        pd.DataFrame(columns=PER_QUERY_COLUMNS).to_csv(per_query_path, index=False)
    write_construction_summary(pairs_df, skipped_df, args)
    return pairs_df, skipped_df


def _make_llm(backend: str, model: str):
    if backend == "together":
        from src.together_llm import TogetherLLM

        return TogetherLLM(model=model, temperature=0.0)
    if backend == "groq":
        from src.groq_llm import GroqLLM

        return GroqLLM(model=model, temperature=0.0)
    from langchain_ollama import OllamaLLM

    base_url = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST")
    if base_url:
        if not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"
        return OllamaLLM(model=model, temperature=0.0, base_url=base_url)
    return OllamaLLM(model=model, temperature=0.0)


def _iter_generation_sets(row: pd.Series) -> Iterable[Tuple[str, List[str], float, float, str]]:
    yield (
        "high_ccs",
        json.loads(row["high_passages_json"]),
        float(row["mean_sim_high"]),
        float(row["ccs_high"]),
        row["high_idxs"],
    )
    yield (
        "low_ccs",
        json.loads(row["low_passages_json"]),
        float(row["mean_sim_low"]),
        float(row["ccs_low"]),
        row["low_idxs"],
    )


def generate_from_pairs(args: argparse.Namespace,
                        pairs_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    _ensure_dirs()
    if pairs_df is None:
        matched_path = Path(args.matched_pairs)
        if not matched_path.exists():
            raise FileNotFoundError(f"Missing matched-pair file: {matched_path}")
        pairs_df = pd.read_csv(matched_path)

    if pairs_df.empty:
        raise RuntimeError("No matched pairs available for generation")
    if args.pair_start is not None or args.pair_end is not None:
        start = 0 if args.pair_start is None else int(args.pair_start)
        end = len(pairs_df) if args.pair_end is None else int(args.pair_end)
        pairs_df = pairs_df.iloc[start:end].copy()
        if pairs_df.empty:
            raise RuntimeError(f"No matched pairs in requested slice [{start}:{end}]")

    llm = _make_llm(args.backend, args.model)
    detector = HallucinationDetector()

    existing = pd.DataFrame()
    out_path = Path(args.per_query_out) if args.per_query_out else OUT_DATA / "per_query.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    completed: set[Tuple[str, str]] = set()
    if args.resume and out_path.exists():
        existing = pd.read_csv(out_path)
        if {"pair_id", "set_type"}.issubset(existing.columns):
            completed = set(zip(existing["pair_id"], existing["set_type"]))

    rows: List[Dict[str, Any]] = []
    t0 = time.time()
    for i, row in pairs_df.iterrows():
        for set_type, passages, mean_sim, ccs, passage_idxs in _iter_generation_sets(row):
            key = (row["pair_id"], set_type)
            if key in completed:
                continue
            context = "\n\n---\n\n".join(passages)
            prompt = RAG_PROMPT.format(context=context, question=row["question"])
            try:
                gen_t0 = time.time()
                answer = llm.invoke(prompt)
                latency = time.time() - gen_t0
                nli = detector.detect(answer, context)
            except Exception as exc:
                rows.append({
                    "pair_id": row["pair_id"],
                    "dataset": row["dataset"],
                    "question": row["question"],
                    "set_type": set_type,
                    "error": f"{type(exc).__name__}:{exc}",
                })
                continue

            rows.append({
                "pair_id": row["pair_id"],
                "dataset": row["dataset"],
                "query_index": int(row["query_index"]),
                "question": row["question"],
                "ground_truth": row.get("ground_truth", ""),
                "model": args.model,
                "backend": args.backend,
                "seed": int(row["seed"]),
                "set_type": set_type,
                "passage_idxs": passage_idxs,
                "mean_query_sim": round(mean_sim, 6),
                "ccs": round(ccs, 6),
                "sim_gap": float(row["sim_gap"]),
                "ccs_gap": float(row["ccs_gap"]),
                "overlap": int(row["overlap"]),
                "answer": answer,
                "faithfulness_score": float(nli["faithfulness_score"]),
                "is_hallucination": bool(nli["is_hallucination"]),
                "nli_label": nli.get("label", ""),
                "latency_s": round(float(latency), 3),
                "error": "",
            })

        if (i + 1) % args.save_every == 0:
            partial = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
            partial.to_csv(out_path, index=False)
            print(
                f"[Fix01/generate] saved {len(partial)} rows "
                f"after {i + 1}/{len(pairs_df)} pairs",
                flush=True,
            )

    df = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
    df.to_csv(out_path, index=False)
    print(
        f"[Fix01/generate] wrote {len(df)} rows in {time.time() - t0:.1f}s",
        flush=True,
    )
    return df


def _cohens_dz(diffs: np.ndarray) -> float:
    if len(diffs) < 2:
        return float("nan")
    denom = diffs.std(ddof=1)
    if denom <= 0 or not np.isfinite(denom):
        return float("nan")
    return float(diffs.mean() / denom)


def _bootstrap_ci(values: np.ndarray,
                  n_resamples: int = N_BOOTSTRAP,
                  seed: int = 42) -> Tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, values.size, size=(n_resamples, values.size))
    means = values[idx].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def analyze_results(args: argparse.Namespace) -> Tuple[pd.DataFrame, pd.DataFrame]:
    _ensure_dirs()
    per_query_path = OUT_DATA / "per_query.csv"
    pairs_path = OUT_DATA / "matched_pairs.csv"
    if not per_query_path.exists():
        print("[Fix01/analyze] per_query.csv is absent; construction-only analysis.")
        pairs_df = _safe_read_csv(pairs_path)
        skipped_path = OUT_DATA / "skipped_queries.csv"
        skipped_df = _safe_read_csv(skipped_path)
        write_construction_summary(pairs_df, skipped_df, args)
        return pd.DataFrame(), pd.DataFrame()

    df = pd.read_csv(per_query_path)
    scored = df[df.get("error", "").fillna("").astype(str).eq("")]
    scored = scored.dropna(subset=["faithfulness_score"])
    rows: List[Dict[str, Any]] = []
    boot_rows: List[Dict[str, Any]] = []

    for dataset, sub in scored.groupby("dataset"):
        high = sub[sub["set_type"] == "high_ccs"].set_index("pair_id")
        low = sub[sub["set_type"] == "low_ccs"].set_index("pair_id")
        common = high.index.intersection(low.index)
        if len(common) < 5:
            continue
        high = high.loc[common]
        low = low.loc[common]
        diffs = (
            high["faithfulness_score"].to_numpy(dtype=float)
            - low["faithfulness_score"].to_numpy(dtype=float)
        )
        sim_diffs = (
            high["mean_query_sim"].to_numpy(dtype=float)
            - low["mean_query_sim"].to_numpy(dtype=float)
        )
        try:
            stat, p_value = wilcoxon(diffs, alternative="greater")
        except ValueError:
            stat, p_value = float("nan"), float("nan")
        try:
            sim_stat, sim_p = wilcoxon(sim_diffs, alternative="two-sided")
        except ValueError:
            sim_stat, sim_p = float("nan"), float("nan")

        hi_h = high["is_hallucination"].astype(bool).to_numpy()
        lo_h = low["is_hallucination"].astype(bool).to_numpy()
        low_only = int((lo_h & ~hi_h).sum())
        high_only = int((hi_h & ~lo_h).sum())
        matched_or = (low_only + 0.5) / (high_only + 0.5)
        ci_lo, ci_hi = _bootstrap_ci(diffs, seed=args.seed)

        row = {
            "dataset": dataset,
            "n_pairs": int(len(common)),
            "mean_faith_high": round(float(high["faithfulness_score"].mean()), 6),
            "mean_faith_low": round(float(low["faithfulness_score"].mean()), 6),
            "mean_diff_high_minus_low": round(float(diffs.mean()), 6),
            "wilcoxon_stat": None if not np.isfinite(stat) else round(float(stat), 6),
            "wilcoxon_p_greater": None if not np.isfinite(p_value) else float(p_value),
            "cohens_dz": round(_cohens_dz(diffs), 6),
            "boot_ci95_lo": round(ci_lo, 6),
            "boot_ci95_hi": round(ci_hi, 6),
            "hallucination_rate_high": round(float(hi_h.mean()), 6),
            "hallucination_rate_low": round(float(lo_h.mean()), 6),
            "matched_odds_ratio_low_vs_high": round(float(matched_or), 6),
            "discordant_low_only": low_only,
            "discordant_high_only": high_only,
            "mean_similarity_delta_high_minus_low": round(float(sim_diffs.mean()), 6),
            "max_abs_similarity_delta": round(float(np.abs(sim_diffs).max()), 6),
            "similarity_wilcoxon_stat": None if not np.isfinite(sim_stat) else round(float(sim_stat), 6),
            "similarity_wilcoxon_p_two_sided": None if not np.isfinite(sim_p) else float(sim_p),
        }
        dz = row["cohens_dz"]
        row["h1_supported"] = bool(
            row["wilcoxon_p_greater"] is not None
            and row["wilcoxon_p_greater"] < 0.05
            and np.isfinite(dz)
            and dz > 0.2
            and row["boot_ci95_lo"] > 0
            and row["max_abs_similarity_delta"] <= SIM_TOL + 1e-9
        )
        rows.append(row)
        boot_rows.append({
            "dataset": dataset,
            "n_pairs": int(len(common)),
            "n_resamples": N_BOOTSTRAP,
            "statistic": "mean_diff_high_minus_low",
            "estimate": row["mean_diff_high_minus_low"],
            "ci95_lo": row["boot_ci95_lo"],
            "ci95_hi": row["boot_ci95_hi"],
        })

    paired_df = pd.DataFrame(rows, columns=PAIRED_COLUMNS)
    boot_df = pd.DataFrame(boot_rows, columns=BOOT_COLUMNS)
    paired_df.to_csv(OUT_RESULTS / "paired_wilcoxon.csv", index=False)
    boot_df.to_csv(OUT_RESULTS / "bootstrap_ci.csv", index=False)
    write_match_diagnostics()
    write_summary_md(paired_df)
    plot_paired_diff(scored)
    return paired_df, boot_df


def write_match_diagnostics() -> None:
    path = OUT_DATA / "matched_pairs.csv"
    if not path.exists():
        pd.DataFrame().to_csv(OUT_RESULTS / "match_diagnostics.csv", index=False)
        return
    pairs = _safe_read_csv(path)
    if pairs.empty:
        pairs.to_csv(OUT_RESULTS / "match_diagnostics.csv", index=False)
        return
    rows = []
    for dataset, sub in pairs.groupby("dataset"):
        rows.append({
            "dataset": dataset,
            "n_pairs_constructed": int(len(sub)),
            "mean_sim_high": round(float(sub["mean_sim_high"].mean()), 6),
            "mean_sim_low": round(float(sub["mean_sim_low"].mean()), 6),
            "mean_abs_sim_gap": round(float(sub["sim_gap"].abs().mean()), 6),
            "max_abs_sim_gap": round(float(sub["sim_gap"].abs().max()), 6),
            "mean_ccs_high": round(float(sub["ccs_high"].mean()), 6),
            "mean_ccs_low": round(float(sub["ccs_low"].mean()), 6),
            "mean_ccs_gap": round(float(sub["ccs_gap"].mean()), 6),
            "min_ccs_gap": round(float(sub["ccs_gap"].min()), 6),
            "mean_overlap": round(float(sub["overlap"].mean()), 6),
            "max_overlap": int(sub["overlap"].max()),
            "mean_bucket_size": round(float(sub["bucket_size"].mean()), 2),
        })
    pd.DataFrame(rows).to_csv(OUT_RESULTS / "match_diagnostics.csv", index=False)


def write_construct_only_per_query(pairs_df: pd.DataFrame) -> None:
    rows: List[Dict[str, Any]] = []
    for _, row in pairs_df.iterrows():
        for set_type, passages, mean_sim, ccs, passage_idxs in _iter_generation_sets(row):
            rows.append({
                "pair_id": row["pair_id"],
                "dataset": row["dataset"],
                "query_index": int(row["query_index"]),
                "question": row["question"],
                "ground_truth": row.get("ground_truth", ""),
                "model": "",
                "backend": "",
                "seed": int(row["seed"]),
                "set_type": set_type,
                "passage_idxs": passage_idxs,
                "mean_query_sim": round(mean_sim, 6),
                "ccs": round(ccs, 6),
                "sim_gap": float(row["sim_gap"]),
                "ccs_gap": float(row["ccs_gap"]),
                "overlap": int(row["overlap"]),
                "answer": "",
                "faithfulness_score": "",
                "is_hallucination": "",
                "nli_label": "",
                "latency_s": "",
                "error": "not_generated_construct_only",
                "context_passages_json": json.dumps(passages),
            })
    pd.DataFrame(rows).to_csv(OUT_DATA / "per_query_construct_only.csv", index=False)


def write_construction_summary(pairs_df: pd.DataFrame,
                               skipped_df: pd.DataFrame,
                               args: argparse.Namespace) -> None:
    write_match_diagnostics()
    diag_df = _safe_read_csv(OUT_RESULTS / "match_diagnostics.csv")
    rows = [{
        "dataset": getattr(args, "dataset", "squad"),
        "stage": "construct",
        "n_target": int(getattr(args, "n_target", 0)),
        "n_pairs_constructed": int(len(pairs_df)),
        "n_skipped": int(len(skipped_df)),
        "max_contexts": int(getattr(args, "max_contexts", 0)),
        "candidate_limit": int(getattr(args, "candidate_limit", 0)),
        "seed": int(getattr(args, "seed", 42)),
        "top_n": TOP_N,
        "triple_k": TRIPLE_K,
        "sim_tolerance": SIM_TOL,
        "ccs_gap_min": CCS_GAP_MIN,
    }]
    pd.DataFrame(rows).to_csv(OUT_RESULTS / "construction_summary.csv", index=False)
    lines = [
        "# Fix 1 - construction summary",
        "",
        "This is the construction-only status for the matched-similarity",
        "HIGH/LOW CCS intervention. It does not include generation or NLI",
        "faithfulness yet.",
        "",
        "## Run",
        "",
        pd.DataFrame(rows).to_markdown(index=False),
        "",
        "## Match Diagnostics",
        "",
        diag_df.to_markdown(index=False) if not diag_df.empty else "(no pairs constructed)",
        "",
        "## Interpretation",
        "",
        "Successful construction means the causal experiment is feasible:",
        "the retrieved top-20 pools contain HIGH/LOW CCS triples whose mean",
        "query similarity differs by no more than 0.02. It does not answer",
        "the causal hypothesis until the generator and NLI scorer are run.",
    ]
    (OUT_RESULTS / "summary.md").write_text("\n".join(lines) + "\n")


def write_summary_md(paired_df: pd.DataFrame) -> None:
    diag_path = OUT_RESULTS / "match_diagnostics.csv"
    diag_df = _safe_read_csv(diag_path)
    lines = [
        "# Fix 1 - causal coherence intervention",
        "",
        "This experiment tests whether HIGH-CCS contexts produce more faithful",
        "answers than LOW-CCS contexts when mean per-passage query similarity is",
        "matched within +/-0.02.",
        "",
        "## Match diagnostics",
        "",
        diag_df.to_markdown(index=False) if not diag_df.empty else "(no constructed pairs yet)",
        "",
        "## Paired faithfulness test",
        "",
        paired_df.to_markdown(index=False) if not paired_df.empty else "(generation/NLI not run yet)",
        "",
        "Decision rule: H1 is supported only when the one-sided paired Wilcoxon",
        "p-value is < 0.05, Cohen's dz is > 0.2, the 10000-resample bootstrap",
        "CI on the mean paired difference excludes 0, and the max similarity",
        "gap remains <= 0.02 by construction.",
        "",
        "If this rule fails, the paper must downgrade causal/mechanistic wording.",
    ]
    (OUT_RESULTS / "summary.md").write_text("\n".join(lines) + "\n")


def plot_paired_diff(df: pd.DataFrame) -> None:
    if df.empty or "faithfulness_score" not in df.columns:
        return
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f"[Fix01/plot] skipped: {exc}")
        return

    fig, ax = plt.subplots(figsize=(5.0, 5.0))
    for dataset, sub in df.groupby("dataset"):
        high = sub[sub["set_type"] == "high_ccs"].set_index("pair_id")
        low = sub[sub["set_type"] == "low_ccs"].set_index("pair_id")
        common = high.index.intersection(low.index)
        if len(common) == 0:
            continue
        ax.scatter(
            low.loc[common, "faithfulness_score"],
            high.loc[common, "faithfulness_score"],
            s=16,
            alpha=0.45,
            label=f"{dataset} (n={len(common)})",
        )
    ax.plot([0, 1], [0, 1], linestyle="--", linewidth=0.8, color="black")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("LOW-CCS faithfulness")
    ax.set_ylabel("HIGH-CCS faithfulness")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_FIG)
    plt.close(fig)


def write_columns_doc() -> None:
    doc = """# Fix 1 column documentation

## `data/revision/fix_01/matched_pairs.csv`

One row per constructed query pair.

| column | description |
| --- | --- |
| `pair_id` | Stable SHA-1 based identifier for the query pair. |
| `dataset` | Dataset name; preregistered primary cell is `squad`. |
| `query_index` | Index of the QA pair in the loaded dataset list before shuffling. |
| `question` | Original query. |
| `ground_truth` | Reference answer when available. |
| `seed` | Query-shuffling seed. |
| `n_candidates` | Number of retrieved passages available; must be at least 20. |
| `n_triples_evaluated` | Number of enumerated 3-passage triples, normally C(20,3)=1140. |
| `bucket_id`, `bucket_size` | Similarity bucket selected by the combinatorial search. |
| `high_idxs`, `low_idxs` | JSON lists of source ranks from the top-20 retrieval pool. |
| `high_passages_json`, `low_passages_json` | JSON lists of the three passage texts used for generation. |
| `mean_sim_high`, `mean_sim_low` | Mean query-passage cosine similarity for each triple. |
| `sim_gap` | Absolute mean-similarity gap; preregistered maximum is 0.02. |
| `ccs_high`, `ccs_low`, `ccs_gap` | Context Coherence Score values and gap. |
| `overlap` | Number of shared passages between HIGH and LOW triples; maximum is 1. |
| `top20_*_query_sim` | Diagnostics over the full retrieved top-20 pool. |
| `construction_version` | Version label for the matching algorithm. |

## `data/revision/fix_01/per_query.csv`

Two rows per generated query pair, one for `high_ccs` and one for `low_ccs`.

| column | description |
| --- | --- |
| `pair_id`, `dataset`, `query_index`, `question`, `ground_truth`, `seed` | Pair metadata copied from `matched_pairs.csv`. |
| `model`, `backend` | Generator and serving backend. |
| `set_type` | `high_ccs` or `low_ccs`. |
| `passage_idxs` | JSON source ranks in the top-20 pool. |
| `mean_query_sim`, `ccs`, `sim_gap`, `ccs_gap`, `overlap` | Matching diagnostics. |
| `answer` | Generated answer from the three-passage context. |
| `faithfulness_score` | DeBERTa-v3 NLI mean entailment score. |
| `is_hallucination` | Boolean thresholded at faithfulness < 0.5. |
| `nli_label` | Detector label (`faithful` or `hallucinated`). |
| `latency_s` | Generator invocation latency. |
| `error` | Empty on success; populated for failed generation/scoring rows. |

## `data/revision/fix_01/skipped_queries.csv`

One row per attempted query that did not yield a matched pair, with `reason`.
"""
    (OUT_DATA / "COLUMNS.md").write_text(doc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["construct", "generate", "full", "analyze"],
                        default="construct")
    parser.add_argument("--dataset", default="squad")
    parser.add_argument("--n_target", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_contexts", type=int, default=400)
    parser.add_argument("--candidate_limit", type=int, default=400)
    parser.add_argument("--persist_dir", default=None)
    parser.add_argument("--run_tag", default=None)
    parser.add_argument("--backend", choices=["ollama", "together", "groq"], default="ollama")
    parser.add_argument("--model", default="mistral")
    parser.add_argument("--matched_pairs", default=str(OUT_DATA / "matched_pairs.csv"))
    parser.add_argument("--per_query_out", default=None,
                        help="Optional output CSV for generation/analyze; useful for sharded runs.")
    parser.add_argument("--pair_start", type=int, default=None,
                        help="Optional zero-based matched-pair slice start for generation.")
    parser.add_argument("--pair_end", type=int, default=None,
                        help="Optional zero-based matched-pair slice end for generation.")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--save_every", type=int, default=10)
    parser.add_argument("--progress_every", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _ensure_dirs()
    write_columns_doc()

    pairs_df: Optional[pd.DataFrame] = None
    if args.stage in {"construct", "full"}:
        pairs_df, _ = construct_pairs(args)
    if args.stage in {"generate", "full"}:
        per_query_df = generate_from_pairs(args, pairs_df)
        print(f"[Fix01] generated rows: {len(per_query_df)}")
    if args.stage in {"analyze", "generate", "full", "construct"}:
        paired_df, _ = analyze_results(args)
        if not paired_df.empty:
            print(paired_df.to_string(index=False))
        else:
            print("[Fix01] no paired faithfulness analysis yet")


if __name__ == "__main__":
    main()
