"""
experiments/run_multiseed_variance.py — Phase 2 Item 5 (variance bars)
=======================================================================

Purpose
-------
Reviewers for NeurIPS will ask: *"is the ~1 pp paradox drop reproducible, or
within noise?"*  We answer by re-running baseline / hcpc_v1 / hcpc_v2 on a
small but diverse datamix with N different generator seeds and reporting
mean ± std per condition.

What varies across seeds
------------------------
Only the **generator's sampling seed** changes.  Retrieval is deterministic
(same embedder, same vectorstore, same top-k), so variance here is a clean
measure of "how much does the LLM's stochastic decoding move our numbers
around" — exactly what a reviewer wants to see error bars on.

To keep the wall-clock budget sane we:
    • run fewer datasets by default (squad + pubmedqa),
    • cap N=30 questions per dataset,
    • test 3 seeds (41, 42, 43).

Budget: 3 conditions × 30 Q × 2 datasets × 3 seeds ≈ 540 generations ≈
45-60 min on the M4 with Mistral-7B.

Outputs (results/multiseed/)
----------------------------
    seed_{s}_per_query.csv     — raw rows per seed
    variance_summary.csv       — mean & std across seeds, per (ds, cond)
    variance_summary.md        — markdown table for paper §Results

Design notes
------------
* We reach into `pipeline.llm` and build a fresh OllamaLLM with the seed
  after `RAGPipeline.__init__`, rather than modifying RAGPipeline.  This
  keeps the change surgical and reversible.
* We DO NOT rebuild the ChromaDB per seed — the index is seed-independent,
  and re-indexing would dominate the runtime budget.
* We pass `seed` both to OllamaLLM (which forwards it to `num_seed` in the
  Ollama API) and to `random` / `numpy` for any ancillary sampling in
  retrievers.  HCPCv2's refinement path is deterministic given the docs
  but we seed it anyway for reproducibility's sake.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import os
import random
from typing import Dict, List

import pandas as pd

from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.retrieval_metrics import compute_retrieval_quality

OUT_DIR = "results/multiseed"

V1_SIM = 0.50
V1_CE  = 0.00
V2_SIM = 0.45
V2_CE  = -0.20
CHUNK_SIZE = 1024
TOP_K = 3


# ─────────────────────────────────────────────────────────────────────────────
# Seeding helpers
# ─────────────────────────────────────────────────────────────────────────────

def _seed_python(seed: int) -> None:
    """Seed stdlib `random` + numpy if present.  Torch is seeded too because
    the NLI detector uses HF transformers under the hood; seeding it is
    cheap insurance against dropout-style non-determinism."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def _reseed_ollama(pipeline: RAGPipeline, seed: int) -> None:
    """Swap pipeline.llm for a fresh OllamaLLM bound to `seed`.

    langchain-ollama forwards unknown kwargs to the Ollama options block, so
    `seed=` becomes `options.seed` in the request. A matching temperature is
    preserved to keep decoding comparable to the un-seeded baseline run.
    """
    from langchain_ollama import OllamaLLM
    pipeline.llm = OllamaLLM(
        model=pipeline.model_name,
        temperature=0.1,
        seed=seed,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Per-query runner (mirrors run_multidataset_validation._eval_one_query)
# ─────────────────────────────────────────────────────────────────────────────

def _eval_one_query(pipeline, qa, retriever, label, detector) -> Dict:
    if retriever is None:
        docs, _sims = pipeline.retrieve_with_scores(qa["question"])
        hlog = {}
    else:
        out = retriever.retrieve(qa["question"])
        if isinstance(out, tuple):
            docs, hlog = out
        else:
            docs, hlog = out, {}
    gen = pipeline.generate(qa["question"], docs)
    nli = detector.detect(gen["answer"], gen["context"])
    ret_m = compute_retrieval_quality(qa["question"], docs, pipeline.embeddings)
    return {
        "question":           qa["question"],
        "ground_truth":       qa.get("ground_truth", ""),
        "answer":             gen["answer"],
        "condition":          label,
        "faithfulness_score": nli["faithfulness_score"],
        "is_hallucination":   nli["is_hallucination"],
        "mean_retrieval_similarity": ret_m.get("mean_similarity", 0.0),
        "refined":            bool(hlog.get("refined", False)) if isinstance(hlog, dict) else False,
        "ccs":                hlog.get("context_coherence", -1.0) if isinstance(hlog, dict) else -1.0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# One-seed one-dataset sweep
# ─────────────────────────────────────────────────────────────────────────────

def run_one(ds: str, model: str, seed: int, n_q: int,
            detector: HallucinationDetector) -> List[Dict]:
    print(f"\n[MS] seed={seed}  dataset={ds}  model={model}")
    docs, qa = load_dataset_by_name(ds, max_papers=30)
    if not docs or not qa:
        print(f"[MS] {ds}: no data — skipping.")
        return []

    coll = f"ms_{ds}_{model}_s{seed}"
    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=TOP_K,
        model_name=model,
        persist_dir=f"./chroma_db_ms/{coll}",
    )
    pipeline.index_documents(docs, collection_name=coll)
    _reseed_ollama(pipeline, seed)

    v1 = HCPCRetriever(pipeline=pipeline, sim_threshold=V1_SIM, ce_threshold=V1_CE,
                       sub_chunk_size=256, sub_chunk_overlap=32, top_k=TOP_K)
    v2 = HCPCv2Retriever(pipeline=pipeline, sim_threshold=V2_SIM, ce_threshold=V2_CE,
                         top_k_protected=2, max_refine=2,
                         sub_chunk_size=256, sub_chunk_overlap=32)

    rows: List[Dict] = []
    for qa_pair in qa[:n_q]:
        for label, retr in [("baseline", None), ("hcpc_v1", v1), ("hcpc_v2", v2)]:
            try:
                rec = _eval_one_query(pipeline, qa_pair, retr, label, detector)
                rec["dataset"] = ds
                rec["model"] = model
                rec["seed"] = seed
                rows.append(rec)
            except Exception as exc:
                print(f"[MS] err {ds}/{label}/{seed}: {exc}")
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Variance aggregation
# ─────────────────────────────────────────────────────────────────────────────

def aggregate_variance(all_rows: List[Dict]) -> pd.DataFrame:
    """Mean & std across seeds for each (dataset, condition).

    Strategy: first collapse within each seed to a (seed, ds, cond) mean,
    then compute mean / std of those per-seed means.  That's the right
    granularity for error bars — std-of-means, not std-of-raw-rows.
    """
    df = pd.DataFrame(all_rows)
    if df.empty:
        return df
    per_seed = (df.groupby(["seed", "dataset", "condition"], as_index=False)
                  .agg(faith=("faithfulness_score", "mean"),
                       halluc=("is_hallucination", "mean"),
                       sim=("mean_retrieval_similarity", "mean"),
                       refine_rate=("refined", "mean")))
    out = (per_seed.groupby(["dataset", "condition"], as_index=False)
                   .agg(n_seeds=("seed", "nunique"),
                        faith_mean=("faith", "mean"),
                        faith_std=("faith", "std"),
                        halluc_mean=("halluc", "mean"),
                        halluc_std=("halluc", "std"),
                        refine_mean=("refine_rate", "mean")))
    for c in ("faith_mean", "faith_std", "halluc_mean", "halluc_std", "refine_mean"):
        out[c] = out[c].round(4)
    return out


def paradox_with_variance(variance: pd.DataFrame) -> pd.DataFrame:
    """Per-dataset baseline vs v1 vs v2, with sqrt(sum of variances) as the
    propagated std on the drop — the usual error-prop for a difference of
    independent means."""
    if variance.empty:
        return variance
    rows = []
    for ds, sub in variance.groupby("dataset"):
        try:
            b  = sub[sub["condition"] == "baseline"].iloc[0]
            v1 = sub[sub["condition"] == "hcpc_v1"].iloc[0]
            v2 = sub[sub["condition"] == "hcpc_v2"].iloc[0]
        except IndexError:
            continue
        drop = b["faith_mean"] - v1["faith_mean"]
        drop_std = float((b["faith_std"] ** 2 + v1["faith_std"] ** 2) ** 0.5)
        recover = v2["faith_mean"] - v1["faith_mean"]
        recover_std = float((v2["faith_std"] ** 2 + v1["faith_std"] ** 2) ** 0.5)
        rows.append({
            "dataset": ds,
            "paradox_drop":    round(drop, 4),
            "paradox_drop_std": round(drop_std, 4),
            "v2_recovery":     round(recover, 4),
            "v2_recovery_std": round(recover_std, 4),
            "significant_drop": bool(abs(drop) > 2 * drop_std),
        })
    return pd.DataFrame(rows)


def write_markdown(variance: pd.DataFrame, paradox: pd.DataFrame, path: str) -> None:
    lines = [
        "# Multi-seed variance (Item 5 — reviewer error bars)",
        "",
        "`faith_std` and `halluc_std` are std-of-seed-means (not std of raw queries).",
        "`significant_drop` ≈ |paradox_drop| > 2·σ (≈ p<0.05 single-tail).",
        "",
        "## Per-condition variance",
        "",
        variance.to_markdown(index=False) if not variance.empty else "(no data)",
        "",
        "## Coherence paradox with error bars",
        "",
        paradox.to_markdown(index=False) if not paradox.empty else "(no data)",
        "",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa"])
    ap.add_argument("--model", default="mistral")
    ap.add_argument("--seeds", nargs="+", type=int, default=[41, 42, 43])
    ap.add_argument("--n_questions", type=int, default=30)
    ap.add_argument("--out_dir", default=OUT_DIR)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    detector = HallucinationDetector()

    all_rows: List[Dict] = []
    for seed in args.seeds:
        _seed_python(seed)
        seed_rows: List[Dict] = []
        for ds in args.datasets:
            if ds not in DATASET_REGISTRY:
                print(f"[MS] unknown dataset {ds}, skipping")
                continue
            seed_rows.extend(run_one(ds, args.model, seed,
                                     args.n_questions, detector))
        # Per-seed checkpoint so a crash late in seed 43 doesn't lose seed 41/42.
        if seed_rows:
            pd.DataFrame(seed_rows).to_csv(
                os.path.join(args.out_dir, f"seed_{seed}_per_query.csv"),
                index=False,
            )
        all_rows.extend(seed_rows)

    if not all_rows:
        raise SystemExit("[MS] no rows collected — check dataset loaders + Ollama.")

    pd.DataFrame(all_rows).to_csv(
        os.path.join(args.out_dir, "per_query.csv"), index=False)
    variance = aggregate_variance(all_rows)
    variance.to_csv(os.path.join(args.out_dir, "variance_summary.csv"), index=False)
    paradox = paradox_with_variance(variance)
    paradox.to_csv(os.path.join(args.out_dir, "paradox_variance.csv"), index=False)
    write_markdown(variance, paradox,
                   os.path.join(args.out_dir, "variance_summary.md"))
    print(f"[MS] outputs -> {args.out_dir}/")


if __name__ == "__main__":
    main()
