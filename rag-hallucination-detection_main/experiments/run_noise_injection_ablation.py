"""
run_noise_injection_ablation.py — NeurIPS Gap 1
===============================================

Disentangles the coherence paradox from a generic noise / irrelevant-
context failure mode.

For each base retrieval of K passages we construct four conditions:

    noise_rate = 0      — baseline (K relevant passages, as usual)
    noise_rate = 1/K    — replace 1 of K with a random off-topic passage
    noise_rate = 2/K    — replace 2 of K
    noise_rate = K/K    — replace all K (pure-noise control)

Off-topic passages are sampled from the SAME corpus but from documents
whose `paper_id` does not match any retrieval result for the query (i.e.
topically unrelated to both the query and the retrieved context).  This
avoids cross-domain contamination artifacts.

Expected outcomes and interpretation:

    (a) If faith(noise_rate) drops smoothly and linearly, the paradox
        is just one instance of a broader "noise hurts faithfulness"
        phenomenon — a threat to the coherence-specific framing.

    (b) If the paradox gap (faith_baseline − faith_v1) exceeds the slope
        |d faith / d noise_rate| by ≥ 2×, coherence is a distinct
        failure mode that cannot be explained by generic noise.

The output table isolates (b) quantitatively, directly addressing the
reviewer question "is it coherence or just noise?".

Outputs (results/noise_injection/):
    per_query.csv           — one row per (dataset, noise_rate, question)
    summary.csv             — aggregated mean ± std per (dataset, noise_rate)
    coherence_vs_noise.csv  — paradox gap vs noise slope per dataset
    summary.md              — narrative + tables for §Ablations

Run (≈ 2 h on M4 across 3 datasets × 4 noise rates × 30 q, mistral only):

    python3 experiments/run_noise_injection_ablation.py \
        --datasets squad pubmedqa hotpotqa \
        --n_questions 30 --top_k 3 --seed 42
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import os
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from langchain_core.documents import Document

from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector


OUTPUT_DIR = "results/noise_injection"
CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, "completed_tuples.json")

CHUNK_SIZE  = 1024
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _load_checkpoint() -> Dict[str, bool]:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as fh:
            return json.load(fh)
    return {}


def _save_checkpoint(state: Dict[str, bool]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as fh:
        json.dump(state, fh, indent=2)


def _build_off_topic_pool(
    docs: List[Document],
    retrieved_paper_ids: set,
    rng: random.Random,
    max_pool: int = 100,
) -> List[Document]:
    """Return documents whose paper_id is disjoint from the retrieval set."""
    pool = [d for d in docs
            if d.metadata.get("paper_id", "") not in retrieved_paper_ids]
    rng.shuffle(pool)
    return pool[:max_pool]


def _inject(
    base_docs: List[Document],
    n_noise: int,
    pool: List[Document],
    rng: random.Random,
) -> List[Document]:
    """Replace `n_noise` of `base_docs` with off-topic docs from `pool`."""
    k = len(base_docs)
    n_noise = min(max(n_noise, 0), k)
    if n_noise == 0 or not pool:
        return list(base_docs)
    indices = rng.sample(range(k), n_noise)
    noisy = list(base_docs)
    for i, j in enumerate(indices):
        noisy[j] = pool[i % len(pool)]
    return noisy


def run_one(
    dataset: str,
    model: str,
    n_questions: int,
    top_k: int,
    seed: int,
    detector: HallucinationDetector,
) -> List[Dict]:
    rng = random.Random(seed)
    print(f"\n{'='*72}\n[Noise] {dataset.upper()} × {model}\n{'='*72}")
    docs, qa = load_dataset_by_name(dataset, max_papers=30)
    if not docs or not qa:
        print(f"[Noise] {dataset}: no data, skipping.")
        return []

    collection = f"noise_{dataset}_{model}"
    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=top_k,
        model_name=model,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_noise/{collection}",
    )
    pipeline.index_documents(docs, collection_name=collection)

    noise_rates = [0, 1, 2, top_k]
    rows: List[Dict] = []
    for qa_pair in qa[:n_questions]:
        base_docs, _ = pipeline.retrieve_with_scores(qa_pair["question"])
        retrieved_ids = {
            d.metadata.get("paper_id", f"_unk_{i}")
            for i, d in enumerate(base_docs)
        }
        pool = _build_off_topic_pool(docs, retrieved_ids, rng)

        for n_noise in noise_rates:
            inj = _inject(base_docs, n_noise, pool, rng)
            try:
                gen = pipeline.generate(qa_pair["question"], inj)
                nli = detector.detect(gen["answer"], gen["context"])
                rows.append({
                    "dataset":    dataset,
                    "model":      model,
                    "n_noise":    n_noise,
                    "noise_rate": round(n_noise / top_k, 3),
                    "question":   qa_pair["question"],
                    "ground_truth": qa_pair.get("ground_truth", ""),
                    "answer":     gen["answer"],
                    "faithfulness_score": nli["faithfulness_score"],
                    "is_hallucination":   nli["is_hallucination"],
                })
            except Exception as exc:
                print(f"[Noise] err {dataset}/{n_noise}: {exc}")
    return rows


def aggregate(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    grp = df.groupby(["dataset", "model", "n_noise", "noise_rate"])
    summary = grp.agg(
        n_queries=("question", "count"),
        faith_mean=("faithfulness_score", "mean"),
        faith_std =("faithfulness_score", "std"),
        halluc_mean=("is_hallucination", "mean"),
    ).reset_index()
    for c in ("faith_mean", "faith_std", "halluc_mean"):
        summary[c] = summary[c].round(4)
    return summary


def coherence_vs_noise_table(
    summary: pd.DataFrame, multidataset_summary_path: str,
) -> pd.DataFrame:
    """Join noise-injection slope against existing paradox gap per dataset."""
    if summary.empty:
        return summary
    # Noise slope: Δfaith per unit noise_rate (linear regression on 4 points).
    rows = []
    for (ds, mdl), sub in summary.groupby(["dataset", "model"]):
        sub = sub.sort_values("noise_rate")
        xs = sub["noise_rate"].to_numpy()
        ys = sub["faith_mean"].to_numpy()
        if len(xs) < 2:
            continue
        slope = float(np.polyfit(xs, ys, 1)[0])
        faith_noise0 = float(sub[sub["n_noise"] == 0]["faith_mean"].iloc[0])
        faith_noiseK = float(sub.iloc[-1]["faith_mean"])
        noise_drop = faith_noise0 - faith_noiseK

        paradox_drop = _paradox_drop_from_summary(
            multidataset_summary_path, ds, mdl)
        rows.append({
            "dataset":        ds,
            "model":          mdl,
            "faith@noise0":   round(faith_noise0, 4),
            "faith@noise1":   round(faith_noiseK, 4),
            "noise_drop":     round(noise_drop, 4),
            "noise_slope":    round(slope, 4),
            "paradox_drop":   paradox_drop,
            "paradox_vs_noise_ratio": (round(paradox_drop / abs(slope), 2)
                                       if abs(slope) > 1e-6 and paradox_drop is not None
                                       else None),
        })
    return pd.DataFrame(rows)


def _paradox_drop_from_summary(path: str, ds: str, mdl: str) -> Optional[float]:
    if not os.path.exists(path):
        return None
    try:
        md = pd.read_csv(path)
    except Exception:
        return None
    sub = md[(md["dataset"] == ds) & (md["model"] == mdl)]
    try:
        base = float(sub[sub["condition"] == "baseline"]["faith"].iloc[0])
        v1   = float(sub[sub["condition"] == "hcpc_v1"]["faith"].iloc[0])
    except (IndexError, KeyError):
        return None
    return round(base - v1, 4)


def write_summary_md(
    summary: pd.DataFrame, coh_vs_noise: pd.DataFrame, out_path: str,
) -> None:
    lines = [
        "# Noise-injection ablation (NeurIPS Gap 1)", "",
        "Replaces {0, 1, 2, K} of K retrieved passages with random off-topic",
        "passages from the same corpus to disentangle the coherence paradox",
        "from generic retrieval noise.", "",
        "## Aggregated faithfulness vs noise rate", "",
        summary.to_markdown(index=False) if not summary.empty else "(no data)", "",
        "## Coherence paradox vs noise sensitivity", "",
        "`noise_slope` = linear regression slope of faithfulness on noise_rate.  ",
        "`paradox_drop` = faith_baseline − faith_v1 from the multidataset run.  ",
        "`paradox_vs_noise_ratio` >= 2 supports the claim that the coherence",
        "paradox is a *distinct failure mode* not explainable by generic noise.", "",
        coh_vs_noise.to_markdown(index=False) if not coh_vs_noise.empty else "(no data)", "",
        "A ratio ≥ 2 across all datasets is the target finding.",
    ]
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+",
                        default=["squad", "pubmedqa", "hotpotqa"])
    parser.add_argument("--model", type=str, default="mistral")
    parser.add_argument("--n_questions", type=int, default=30)
    parser.add_argument("--top_k", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--multidataset_summary", type=str,
                        default="results/multidataset/summary.csv")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    state = _load_checkpoint()
    detector = HallucinationDetector()

    all_rows: List[Dict] = []
    prior = os.path.join(OUTPUT_DIR, "per_query.csv")
    if os.path.exists(prior):
        try:
            all_rows.extend(pd.read_csv(prior).to_dict("records"))
        except Exception:
            pass

    for ds in args.datasets:
        if ds not in DATASET_REGISTRY:
            print(f"[Noise] unknown dataset {ds}"); continue
        key = f"{ds}__{args.model}"
        if state.get(key) and not args.force:
            print(f"[Noise] checkpoint hit, skipping {key}")
            continue
        rows = run_one(ds, args.model, args.n_questions,
                       args.top_k, args.seed, detector)
        all_rows.extend(rows)
        pd.DataFrame(rows).to_csv(
            os.path.join(OUTPUT_DIR, f"{key}_per_query.csv"), index=False
        )
        state[key] = True
        _save_checkpoint(state)

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "per_query.csv"), index=False)
    summary = aggregate(all_rows)
    summary.to_csv(os.path.join(OUTPUT_DIR, "summary.csv"), index=False)
    coh = coherence_vs_noise_table(summary, args.multidataset_summary)
    coh.to_csv(os.path.join(OUTPUT_DIR, "coherence_vs_noise.csv"), index=False)
    write_summary_md(summary, coh, os.path.join(OUTPUT_DIR, "summary.md"))
    print(f"[Noise] outputs -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
