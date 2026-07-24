"""
HCPC Ablation — Hybrid Context-Preserving Chunking vs. Fixed-1024 Baseline
===========================================================================

Controlled comparison between:
  baseline   — fixed 1024-token chunks, standard cosine retrieval
  hcpc       — same 1024-token index, but two-stage selective refinement

For every query the script records:
  • NLI faithfulness score (HallucinationDetector)
  • Is-hallucination flag
  • Retrieval quality metrics (cosine similarity stats)
  • HCPC refinement log (n_weak, n_refined, CE/sim improvements per chunk)
  • Generation latency

Outputs (results/hybrid/)
  ├── squad_baseline.csv         per-query results, baseline
  ├── squad_hcpc.csv             per-query results, HCPC
  ├── pubmedqa_baseline.csv
  ├── pubmedqa_hcpc.csv
  ├── logs/
  │    ├── squad_baseline_logs.json    FailureLogger JSON
  │    ├── squad_hcpc_logs.json
  │    ├── pubmedqa_baseline_logs.json
  │    └── pubmedqa_hcpc_logs.json
  ├── summary.csv                aggregate table: dataset × condition
  └── summary.json               same in JSON

Controlled variables (identical for baseline and HCPC in the same run):
  • Documents indexed          (same set, same 1024-token chunks)
  • Queries evaluated          (same ordered list, same N_QUESTIONS)
  • LLM model                  (MODEL_NAME)
  • Embedding model            (EMBED_MODEL)
  • top_k                      (TOP_K — same for both stages)
  • Prompt template            (RAGPipeline.RAG_PROMPT)
  • Random seed                (datasets loaded deterministically)

Run:
    venv/bin/python3 run_hcpc_ablation.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from __future__ import annotations

import json
import os
import time
from typing import Any

import pandas as pd
from tqdm import tqdm

from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.retrieval_metrics import compute_retrieval_quality
from src.failure_logger import FailureLogger
from src.data_loader import load_qasper
from src.pubmedqa_loader import load_pubmedqa


# ── Experiment parameters ─────────────────────────────────────────────────────
# Keep these identical to the existing fixed-1024 ablation configs for a fair
# apples-to-apples comparison.

N_DOCS       = 30        # source documents indexed per run
N_QUESTIONS  = 30        # queries evaluated per configuration
MODEL_NAME   = "mistral"
EMBED_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K        = 3         # final context chunks for generator
CHUNK_SIZE   = 1024      # matches existing fixed_1024 baseline

# HCPC hyper-parameters
HCPC_SIM_THRESHOLD  = 0.50   # cosine similarity below → weak chunk
HCPC_CE_THRESHOLD   = 0.00   # cross-encoder logit below → weak chunk
HCPC_SUB_CHUNK_SIZE = 256    # sub-split target size (tokens)
HCPC_SUB_OVERLAP    = 32

OUTPUT_DIR = "results/hybrid"
LOG_DIR    = os.path.join(OUTPUT_DIR, "logs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


# ── Baseline run ──────────────────────────────────────────────────────────────

def run_baseline(
    pipeline: RAGPipeline,
    qa_pairs: list[dict],
    detector: HallucinationDetector,
    dataset_name: str,
) -> tuple[list[dict], dict]:
    """
    Standard retrieval: fixed 1024-token chunks, top-k cosine search.
    No refinement.  Mirrors the existing Phase-1 / Phase-2 protocol.
    """
    label    = "baseline"
    log_path = os.path.join(LOG_DIR, f"{dataset_name}_{label}_logs.json")
    logger   = FailureLogger(log_path, log_all=True)
    results: list[dict] = []

    print(f"\n{'='*64}")
    print(f"[HCPC] {dataset_name.upper()} | FIXED-1024 BASELINE")
    print(f"{'='*64}")

    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc="baseline"):
        try:
            t0 = time.time()
            docs, sim_scores = pipeline.retrieve_with_scores(qa["question"])
            gen   = pipeline.generate(qa["question"], docs)
            nli   = detector.detect(gen["answer"], gen["context"])
            ret_m = compute_retrieval_quality(qa["question"], docs, pipeline.embeddings)
            ret_m["chroma_mean_score"] = (
                round(sum(sim_scores) / len(sim_scores), 4) if sim_scores else 0.0
            )

            record: dict = _build_record(
                dataset=dataset_name,
                condition=label,
                qa=qa,
                gen=gen,
                nli=nli,
                ret_m=ret_m,
                extra={
                    "hcpc_n_strong":  len(docs),
                    "hcpc_n_weak":    0,
                    "hcpc_n_refined": 0,
                },
            )
            results.append(record)

            logger.log(
                query=qa["question"],
                retrieved_context=gen["context"],
                generated_output=gen["answer"],
                faithfulness_score=nli["faithfulness_score"],
                is_hallucination=nli["is_hallucination"],
                sentence_scores=nli.get("sentence_scores", []),
                retrieval_metrics=ret_m,
                metadata={
                    "dataset": dataset_name,
                    "condition": label,
                    "chunk_size": CHUNK_SIZE,
                    "top_k": TOP_K,
                    "ground_truth": qa.get("ground_truth", ""),
                },
            )

        except Exception as exc:
            print(f"[HCPC] Warning (baseline query failed): {exc}")

    logger.save()
    logger.to_csv()
    summary = _build_summary(dataset_name, label, results, n_chunks_indexed=None)
    return results, summary


# ── HCPC run ──────────────────────────────────────────────────────────────────

def run_hcpc(
    pipeline: RAGPipeline,
    hcpc: HCPCRetriever,
    qa_pairs: list[dict],
    detector: HallucinationDetector,
    dataset_name: str,
) -> tuple[list[dict], dict]:
    """
    HCPC retrieval: same 1024-token index, two-stage refinement.
    """
    label    = "hcpc"
    log_path = os.path.join(LOG_DIR, f"{dataset_name}_{label}_logs.json")
    logger   = FailureLogger(log_path, log_all=True)
    results: list[dict] = []

    print(f"\n{'='*64}")
    print(f"[HCPC] {dataset_name.upper()} | HCPC (sim≥{HCPC_SIM_THRESHOLD}, "
          f"ce≥{HCPC_CE_THRESHOLD}, sub={HCPC_SUB_CHUNK_SIZE}tok)")
    print(f"{'='*64}")

    all_hcpc_logs: list[dict] = []

    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc="hcpc"):
        try:
            docs, hcpc_log = hcpc.retrieve(qa["question"])
            all_hcpc_logs.append(hcpc_log)

            gen   = pipeline.generate(qa["question"], docs)
            nli   = detector.detect(gen["answer"], gen["context"])
            ret_m = compute_retrieval_quality(qa["question"], docs, pipeline.embeddings)
            ret_m["hcpc_n_weak"]    = hcpc_log["n_weak"]
            ret_m["hcpc_n_refined"] = hcpc_log["n_refined"]

            record: dict = _build_record(
                dataset=dataset_name,
                condition=label,
                qa=qa,
                gen=gen,
                nli=nli,
                ret_m=ret_m,
                extra={
                    "hcpc_n_strong":  hcpc_log["n_strong"],
                    "hcpc_n_weak":    hcpc_log["n_weak"],
                    "hcpc_n_refined": hcpc_log["n_refined"],
                    "hcpc_mean_ce_improvement": (
                        round(
                            sum(r.get("ce_improvement", 0) for r in hcpc_log["refinements"]) /
                            max(len(hcpc_log["refinements"]), 1),
                            4,
                        ) if hcpc_log["refinements"] else 0.0
                    ),
                    "hcpc_mean_sim_improvement": (
                        round(
                            sum(r.get("sim_improvement", 0) for r in hcpc_log["refinements"]) /
                            max(len(hcpc_log["refinements"]), 1),
                            4,
                        ) if hcpc_log["refinements"] else 0.0
                    ),
                },
            )
            results.append(record)

            logger.log(
                query=qa["question"],
                retrieved_context=gen["context"],
                generated_output=gen["answer"],
                faithfulness_score=nli["faithfulness_score"],
                is_hallucination=nli["is_hallucination"],
                sentence_scores=nli.get("sentence_scores", []),
                retrieval_metrics=ret_m,
                metadata={
                    "dataset": dataset_name,
                    "condition": label,
                    "chunk_size": CHUNK_SIZE,
                    "top_k": TOP_K,
                    "ground_truth": qa.get("ground_truth", ""),
                    "hcpc_log": hcpc_log,
                },
            )

        except Exception as exc:
            print(f"[HCPC] Warning (hcpc query failed): {exc}")

    logger.save()
    logger.to_csv()

    # Save HCPC-specific refinement log
    hcpc_detail_path = os.path.join(LOG_DIR, f"{dataset_name}_hcpc_refinements.json")
    with open(hcpc_detail_path, "w") as fh:
        json.dump(all_hcpc_logs, fh, indent=2)
    print(f"[HCPC] Refinement detail → {hcpc_detail_path}")

    # Aggregate HCPC stats
    hcpc_stats = hcpc.summary_stats(all_hcpc_logs)
    print(f"[HCPC] Refinement summary: {hcpc_stats}")

    summary = _build_summary(dataset_name, label, results, n_chunks_indexed=None)
    summary.update({
        "hcpc_pct_queries_refined": hcpc_stats.get("pct_queries_with_refinement", 0.0),
        "hcpc_mean_ce_improvement": hcpc_stats.get("mean_ce_improvement", 0.0),
        "hcpc_mean_sim_improvement": hcpc_stats.get("mean_sim_improvement", 0.0),
        "hcpc_mean_n_weak":         hcpc_stats.get("mean_n_weak_per_query", 0.0),
    })
    return results, summary


# ── Comparison table ──────────────────────────────────────────────────────────

def print_comparison(summaries: list[dict]) -> None:
    """Pretty-print a side-by-side comparison table."""
    df = pd.DataFrame(summaries)
    print("\n" + "=" * 72)
    print("HCPC vs BASELINE — FINAL COMPARISON")
    print("=" * 72)

    for ds in df["dataset"].unique():
        sub = df[df["dataset"] == ds].copy()
        base = sub[sub["condition"] == "baseline"]
        hcpc = sub[sub["condition"] == "hcpc"]

        if base.empty or hcpc.empty:
            print(f"\n  {ds.upper()}: incomplete data")
            continue

        b, h = base.iloc[0], hcpc.iloc[0]
        delta_f = h["nli_faithfulness"] - b["nli_faithfulness"]
        delta_h = h["hallucination_rate"] - b["hallucination_rate"]

        print(f"\n  Dataset: {ds.upper()}")
        print(f"  {'Metric':<30} {'Baseline':>12} {'HCPC':>12} {'Δ':>10}")
        print(f"  {'-'*66}")
        print(f"  {'NLI Faithfulness':<30} {b['nli_faithfulness']:>12.4f} "
              f"{h['nli_faithfulness']:>12.4f} {delta_f:>+10.4f}")
        print(f"  {'Hallucination Rate':<30} {b['hallucination_rate']:>12.1%} "
              f"{h['hallucination_rate']:>12.1%} {delta_h:>+10.1%}")
        print(f"  {'Mean Retrieval Sim':<30} "
              f"{b['mean_retrieval_similarity']:>12.4f} "
              f"{h['mean_retrieval_similarity']:>12.4f} "
              f"{h['mean_retrieval_similarity'] - b['mean_retrieval_similarity']:>+10.4f}")

        if "hcpc_pct_queries_refined" in h:
            print(f"  {'Queries Refined (%)':<30} {'—':>12} "
                  f"{h['hcpc_pct_queries_refined']:>12.1%} {'':>10}")
        if "hcpc_mean_ce_improvement" in h:
            print(f"  {'Mean CE Improvement':<30} {'—':>12} "
                  f"{h['hcpc_mean_ce_improvement']:>12.4f} {'':>10}")
        if "hcpc_mean_sim_improvement" in h:
            print(f"  {'Mean Sim Improvement':<30} {'—':>12} "
                  f"{h['hcpc_mean_sim_improvement']:>12.4f} {'':>10}")


# ── Record builders ───────────────────────────────────────────────────────────

def _build_record(
    dataset: str,
    condition: str,
    qa: dict,
    gen: dict,
    nli: dict,
    ret_m: dict,
    extra: dict,
) -> dict:
    r: dict = {
        "dataset":            dataset,
        "condition":          condition,
        "chunk_size":         CHUNK_SIZE,
        "top_k":              TOP_K,
        "question":           qa["question"],
        "ground_truth":       qa.get("ground_truth", ""),
        "answer":             gen["answer"],
        "faithfulness_score": nli["faithfulness_score"],
        "is_hallucination":   nli["is_hallucination"],
        "nli_label":          nli["label"],
        "latency_s":          gen["latency_s"],
    }
    r.update({f"ret_{k}": v for k, v in ret_m.items()})
    r.update(extra)
    return r


def _build_summary(
    dataset: str,
    condition: str,
    results: list[dict],
    n_chunks_indexed: Any,
) -> dict:
    if not results:
        return {}
    n          = len(results)
    avg_f      = sum(r["faithfulness_score"] for r in results) / n
    halluc     = sum(1 for r in results if r["is_hallucination"]) / n
    avg_sim    = sum(r.get("ret_mean_similarity", 0.0) for r in results) / n
    n_halluc   = sum(1 for r in results if r["is_hallucination"])

    s = {
        "dataset":                   dataset,
        "condition":                 condition,
        "chunk_size":                CHUNK_SIZE,
        "top_k":                     TOP_K,
        "n_queries":                 n,
        "n_hallucinated":            n_halluc,
        "nli_faithfulness":          round(avg_f, 4),
        "hallucination_rate":        round(halluc, 4),
        "mean_retrieval_similarity": round(avg_sim, 4),
    }
    if n_chunks_indexed is not None:
        s["n_chunks_indexed"] = n_chunks_indexed
    print(
        f"[HCPC] {dataset}/{condition} → "
        f"faith={s['nli_faithfulness']:.4f}  "
        f"halluc={s['hallucination_rate']:.1%}  "
        f"sim={s['mean_retrieval_similarity']:.4f}"
    )
    return s


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("[HCPC] Loading datasets...")
    squad_docs,  squad_qa  = load_qasper(max_papers=N_DOCS)
    pubmed_docs, pubmed_qa = load_pubmedqa(max_papers=N_DOCS)

    print("[HCPC] Loading hallucination detector...")
    detector = HallucinationDetector()

    all_results:   list[dict] = []
    all_summaries: list[dict] = []

    datasets = [
        ("squad",    squad_docs,  squad_qa),
        ("pubmedqa", pubmed_docs, pubmed_qa),
    ]

    for ds_name, docs, qa in datasets:
        # ── Build ONE shared index (1024-token chunks) ─────────────────────
        collection_name = f"hcpc_{ds_name}"
        pipeline = RAGPipeline(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=int(CHUNK_SIZE * 0.1),
            top_k=TOP_K,
            model_name=MODEL_NAME,
            embed_model=EMBED_MODEL,
            persist_dir=f"./chroma_db_hcpc/{collection_name}",
        )
        n_chunks = pipeline.index_documents(docs, collection_name=collection_name)
        print(f"[HCPC] {ds_name}: indexed {n_chunks} chunks (1024-token fixed)")

        # ── Baseline (no refinement) ──────────────────────────────────────
        base_results, base_summary = run_baseline(pipeline, qa, detector, ds_name)
        base_summary["n_chunks_indexed"] = n_chunks
        all_results.extend(base_results)
        if base_summary:
            all_summaries.append(base_summary)

        if base_results:
            pd.DataFrame(base_results).to_csv(
                os.path.join(OUTPUT_DIR, f"{ds_name}_baseline.csv"), index=False
            )

        # ── HCPC (two-stage refinement) ───────────────────────────────────
        # HCPCRetriever is initialised ONCE per dataset and reused per query.
        # The cross-encoder is loaded here; shared with both datasets above.
        hcpc = HCPCRetriever(
            pipeline=pipeline,
            sim_threshold=HCPC_SIM_THRESHOLD,
            ce_threshold=HCPC_CE_THRESHOLD,
            sub_chunk_size=HCPC_SUB_CHUNK_SIZE,
            sub_chunk_overlap=HCPC_SUB_OVERLAP,
            top_k=TOP_K,
        )

        hcpc_results, hcpc_summary = run_hcpc(pipeline, hcpc, qa, detector, ds_name)
        hcpc_summary["n_chunks_indexed"] = n_chunks
        all_results.extend(hcpc_results)
        if hcpc_summary:
            all_summaries.append(hcpc_summary)

        if hcpc_results:
            pd.DataFrame(hcpc_results).to_csv(
                os.path.join(OUTPUT_DIR, f"{ds_name}_hcpc.csv"), index=False
            )

    # ── Summary files ──────────────────────────────────────────────────────────
    if all_summaries:
        summary_df = pd.DataFrame(all_summaries)
        summary_df.to_csv(os.path.join(OUTPUT_DIR, "summary.csv"), index=False)
        with open(os.path.join(OUTPUT_DIR, "summary.json"), "w") as fh:
            json.dump(all_summaries, fh, indent=2)

    # ── Comparison table ───────────────────────────────────────────────────────
    if all_summaries:
        print_comparison(all_summaries)

    print(f"\n[HCPC] All outputs written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
