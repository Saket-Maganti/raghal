"""
run_reranker_experiment.py — Reranker Baseline Comparison
==========================================================

Compares four conditions on identical documents, queries, and LLM:

  baseline     — fixed 1024-token chunks, cosine-ranked top-3
  reranker     — over-fetch top-7, cross-encoder rerank → keep top-3
  hcpc_v2      — HCPC-Selective v2 (AND-gate, top-2 lock, merge-back)
  hcpc_v2_rr   — HCPC-v2 retrieval, then cross-encoder rerank of the result

The reranker only changes passage ordering; it never modifies content.
Toggle via RERANKER_ENABLED flag below.

Outputs (results/reranker/)
  ├── per_query.csv         one row per query × condition
  ├── metrics.csv           aggregate: dataset × condition
  ├── summary.md            human-readable table
  └── logs/
       ├── {dataset}_{condition}_logs.json
       └── {dataset}_reranker_diagnostics.json

Run
---
    python3 run_reranker_experiment.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Tuple

import pandas as pd
from tqdm import tqdm

from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.reranker import Reranker
from src.retrieval_metrics import compute_retrieval_quality
from src.failure_logger import FailureLogger
from src.data_loader import load_qasper
from src.pubmedqa_loader import load_pubmedqa

# ── Experiment parameters ─────────────────────────────────────────────────────

N_DOCS           = 30
N_QUESTIONS      = 30
MODEL_NAME       = "llama3"          # use llama3 for lower baseline hallucination
EMBED_MODEL      = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K            = 3
FETCH_K          = 7                 # candidates fetched before reranking
CHUNK_SIZE       = 1024
RERANKER_ENABLED = True              # set False to run cosine-fallback condition

# HCPC v2 defaults (same as run_hcpc_v2_ablation.py)
V2_SIM_THRESHOLD   = 0.45
V2_CE_THRESHOLD    = -0.20
V2_TOP_K_PROTECTED = 2
V2_MAX_REFINE      = 2
V2_SUB_CHUNK_SIZE  = 256
V2_SUB_OVERLAP     = 32

CE_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

OUTPUT_DIR = "results/reranker"
LOG_DIR    = os.path.join(OUTPUT_DIR, "logs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _banner(dataset: str, condition: str) -> None:
    print(f"\n{'='*60}")
    print(f"  Dataset: {dataset.upper()}   Condition: {condition}")
    print(f"{'='*60}")


def _build_record(
    dataset: str,
    condition: str,
    qa: Dict,
    gen: Dict,
    nli: Dict,
    ret_m: Dict,
    extra: Dict | None = None,
) -> Dict:
    rec = {
        "dataset":          dataset,
        "condition":        condition,
        "chunk_size":       CHUNK_SIZE,
        "top_k":            TOP_K,
        "fetch_k":          FETCH_K,
        "question":         qa["question"],
        "ground_truth":     qa.get("answer", qa.get("ground_truth", "")),
        "answer":           gen.get("answer", ""),
        "faithfulness_score": nli.get("faithfulness_score", 0.0),
        "is_hallucination": nli.get("is_hallucination", False),
        "nli_label":        nli.get("label", "unknown"),
        "latency_s":        gen.get("latency_s", 0.0),
    }
    # flatten ret_m
    for k, v in ret_m.items():
        rec[f"ret_{k}"] = v
    if extra:
        rec.update(extra)
    return rec


def _aggregate(rows: List[Dict], dataset: str, condition: str) -> Dict:
    if not rows:
        return {}
    n = len(rows)
    n_hall = sum(1 for r in rows if r.get("is_hallucination"))
    return {
        "dataset":             dataset,
        "condition":           condition,
        "n_queries":           n,
        "n_hallucinated":      n_hall,
        "nli_faithfulness":    round(sum(r["faithfulness_score"] for r in rows) / n, 4),
        "hallucination_rate":  round(n_hall / n * 100, 1),
        "mean_ret_similarity": round(
            sum(r.get("ret_mean_similarity", 0) for r in rows) / n, 4
        ),
        "mean_reranker_ce":    round(
            sum(r.get("reranker_mean_ce_score", -1) for r in rows
                if r.get("reranker_mean_ce_score", -1) >= 0) /
            max(1, sum(1 for r in rows if r.get("reranker_mean_ce_score", -1) >= 0)),
            4,
        ),
        "mean_latency_s":      round(sum(r.get("latency_s", 0) for r in rows) / n, 3),
    }


# ── Run functions ─────────────────────────────────────────────────────────────

def run_baseline(pipeline, qa_pairs, detector, dataset_name):
    label    = "baseline"
    log_path = os.path.join(LOG_DIR, f"{dataset_name}_{label}_logs.json")
    fl       = FailureLogger(log_path, log_all=True)
    results  = []
    _banner(dataset_name, "BASELINE (cosine top-3)")

    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc=f"{dataset_name}/{label}"):
        try:
            docs, scores = pipeline.retrieve_with_scores(qa["question"])
            gen  = pipeline.generate(qa["question"], docs)
            nli  = detector.detect(gen["answer"], gen["context"])
            retm = compute_retrieval_quality(qa["question"], docs, pipeline.embeddings)
            retm["chroma_mean_score"] = (
                round(sum(scores) / len(scores), 4) if scores else 0.0
            )
            rec = _build_record(dataset_name, label, qa, gen, nli, retm,
                                 extra={"reranker_mean_ce_score": -1.0,
                                        "reranker_fetch_k": 0,
                                        "hcpc_refined": False,
                                        "hcpc_context_coherence": -1.0})
            results.append(rec)
            fl.log(qa["question"], gen["context"], gen["answer"],
                   nli["faithfulness_score"], nli["is_hallucination"],
                   nli.get("sentence_scores", []), retm,
                   {"dataset": dataset_name, "condition": label})
        except Exception as e:
            print(f"[WARN] baseline query failed: {e}")
    fl.save()
    fl.to_csv(log_path.replace(".json", ".csv"))
    return results, _aggregate(results, dataset_name, label)


def run_reranker(pipeline, qa_pairs, detector, dataset_name, reranker):
    label    = "reranker"
    log_path = os.path.join(LOG_DIR, f"{dataset_name}_{label}_logs.json")
    fl       = FailureLogger(log_path, log_all=True)
    results  = []
    rr_diags = []
    _banner(dataset_name, f"RERANKER (fetch={FETCH_K} → top-{TOP_K})")

    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc=f"{dataset_name}/{label}"):
        try:
            docs, rr_log = reranker.retrieve_and_rerank(
                qa["question"], pipeline, fetch_k=FETCH_K, top_k=TOP_K
            )
            gen  = pipeline.generate(qa["question"], docs)
            nli  = detector.detect(gen["answer"], gen["context"])
            retm = compute_retrieval_quality(qa["question"], docs, pipeline.embeddings)
            retm["chroma_mean_score"] = 0.0
            rr_diags.append(rr_log)
            rec = _build_record(dataset_name, label, qa, gen, nli, retm,
                                 extra={"reranker_mean_ce_score": rr_log.get("mean_ce_score", -1.0),
                                        "reranker_fetch_k": rr_log.get("fetch_k", FETCH_K),
                                        "hcpc_refined": False,
                                        "hcpc_context_coherence": -1.0})
            results.append(rec)
            fl.log(qa["question"], gen["context"], gen["answer"],
                   nli["faithfulness_score"], nli["is_hallucination"],
                   nli.get("sentence_scores", []), retm,
                   {"dataset": dataset_name, "condition": label})
        except Exception as e:
            print(f"[WARN] reranker query failed: {e}")

    fl.save()
    fl.to_csv(log_path.replace(".json", ".csv"))
    diag_path = os.path.join(LOG_DIR, f"{dataset_name}_reranker_diagnostics.json")
    with open(diag_path, "w") as f:
        json.dump({"reranker_logs": rr_diags,
                   "summary": Reranker.summary_stats(rr_diags)}, f, indent=2)
    return results, _aggregate(results, dataset_name, label)


def run_hcpc_v2(pipeline, qa_pairs, detector, dataset_name):
    label    = "hcpc_v2"
    log_path = os.path.join(LOG_DIR, f"{dataset_name}_{label}_logs.json")
    fl       = FailureLogger(log_path, log_all=True)
    hcpc     = HCPCv2Retriever(
        pipeline,
        sim_threshold=V2_SIM_THRESHOLD,
        ce_threshold=V2_CE_THRESHOLD,
        top_k_protected=V2_TOP_K_PROTECTED,
        max_refine=V2_MAX_REFINE,
        sub_chunk_size=V2_SUB_CHUNK_SIZE,
        sub_chunk_overlap=V2_SUB_OVERLAP,
    )
    results  = []
    v2_diags = []
    _banner(dataset_name, "HCPC-v2 (AND-gate + top-2 lock + merge-back)")

    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc=f"{dataset_name}/{label}"):
        try:
            docs, log = hcpc.retrieve(qa["question"])
            gen  = pipeline.generate(qa["question"], docs)
            nli  = detector.detect(gen["answer"], gen["context"])
            retm = compute_retrieval_quality(qa["question"], docs, pipeline.embeddings)
            retm.update({
                "hcpc_v2_n_refined": log.get("n_refined_chunks", 0),
                "hcpc_v2_n_merged":  log.get("n_merged_chunks", 0),
                "hcpc_v2_context_coherence": log.get("context_coherence", -1.0),
                "chroma_mean_score": 0.0,
            })
            v2_diags.append(log)
            rec = _build_record(dataset_name, label, qa, gen, nli, retm,
                                 extra={"reranker_mean_ce_score": -1.0,
                                        "reranker_fetch_k": 0,
                                        "hcpc_refined":           log.get("refined", False),
                                        "hcpc_n_refined":         log.get("n_refined_chunks", 0),
                                        "hcpc_n_merged":          log.get("n_merged_chunks", 0),
                                        "hcpc_context_coherence": log.get("context_coherence", -1.0)})
            results.append(rec)
            fl.log(qa["question"], gen["context"], gen["answer"],
                   nli["faithfulness_score"], nli["is_hallucination"],
                   nli.get("sentence_scores", []), retm,
                   {"dataset": dataset_name, "condition": label})
        except Exception as e:
            print(f"[WARN] hcpc_v2 query failed: {e}")

    fl.save()
    fl.to_csv(log_path.replace(".json", ".csv"))
    diag_path = os.path.join(LOG_DIR, f"{dataset_name}_hcpc_v2_diagnostics.json")
    with open(diag_path, "w") as f:
        json.dump({"v2_logs": v2_diags,
                   "summary": HCPCv2Retriever.summary_stats(v2_diags)}, f, indent=2)
    return results, _aggregate(results, dataset_name, label)


def run_hcpc_v2_plus_reranker(pipeline, qa_pairs, detector, dataset_name, reranker):
    """HCPC-v2 retrieval then cross-encoder rerank the refined result."""
    label    = "hcpc_v2_rr"
    log_path = os.path.join(LOG_DIR, f"{dataset_name}_{label}_logs.json")
    fl       = FailureLogger(log_path, log_all=True)
    hcpc     = HCPCv2Retriever(
        pipeline,
        sim_threshold=V2_SIM_THRESHOLD,
        ce_threshold=V2_CE_THRESHOLD,
        top_k_protected=V2_TOP_K_PROTECTED,
        max_refine=V2_MAX_REFINE,
        sub_chunk_size=V2_SUB_CHUNK_SIZE,
        sub_chunk_overlap=V2_SUB_OVERLAP,
    )
    results  = []
    _banner(dataset_name, "HCPC-v2 + Reranker")

    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc=f"{dataset_name}/{label}"):
        try:
            docs, hlog = hcpc.retrieve(qa["question"])
            # Apply cross-encoder reranking on the already-refined docs
            reranked_docs = reranker.rerank(qa["question"], docs, top_k=TOP_K)
            gen  = pipeline.generate(qa["question"], reranked_docs)
            nli  = detector.detect(gen["answer"], gen["context"])
            retm = compute_retrieval_quality(qa["question"], reranked_docs, pipeline.embeddings)
            retm.update({
                "hcpc_v2_n_refined":         hlog.get("n_refined_chunks", 0),
                "hcpc_v2_n_merged":          hlog.get("n_merged_chunks", 0),
                "hcpc_v2_context_coherence": hlog.get("context_coherence", -1.0),
                "chroma_mean_score": 0.0,
            })
            rec = _build_record(dataset_name, label, qa, gen, nli, retm,
                                 extra={"reranker_mean_ce_score": -1.0,
                                        "reranker_fetch_k": TOP_K,
                                        "hcpc_refined":           hlog.get("refined", False),
                                        "hcpc_n_refined":         hlog.get("n_refined_chunks", 0),
                                        "hcpc_context_coherence": hlog.get("context_coherence", -1.0)})
            results.append(rec)
            fl.log(qa["question"], gen["context"], gen["answer"],
                   nli["faithfulness_score"], nli["is_hallucination"],
                   nli.get("sentence_scores", []), retm,
                   {"dataset": dataset_name, "condition": label})
        except Exception as e:
            print(f"[WARN] hcpc_v2_rr query failed: {e}")

    fl.save()
    fl.to_csv(log_path.replace(".json", ".csv"))
    return results, _aggregate(results, dataset_name, label)


# ── Dataset runner ────────────────────────────────────────────────────────────

def run_dataset(dataset_name: str, docs_raw, qa_pairs, reranker):
    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=0,
        top_k=TOP_K,
        model_name=MODEL_NAME,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_reranker_{dataset_name}",
    )
    collection_name = f"reranker_{dataset_name}"
    pipeline.index_documents(docs_raw[:N_DOCS], collection_name=collection_name)

    detector = HallucinationDetector()

    all_rows, summaries = [], []
    for run_fn, uses_rr in [
        (run_baseline,           False),
        (run_reranker,           True),
        (run_hcpc_v2,            False),
        (run_hcpc_v2_plus_reranker, True),
    ]:
        if uses_rr:
            rows, agg = run_fn(pipeline, qa_pairs, detector, dataset_name, reranker)
        else:
            rows, agg = run_fn(pipeline, qa_pairs, detector, dataset_name)
        all_rows.extend(rows)
        summaries.append(agg)

    return all_rows, summaries


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n[INFO] Initializing cross-encoder reranker...")
    reranker = Reranker(model_name=CE_MODEL, enabled=RERANKER_ENABLED)

    print("[INFO] Loading datasets...")
    # load_qasper uses max_papers to cap documents; QA pairs are sliced later.
    # load_pubmedqa similarly uses max_papers.
    squad_docs, squad_qa   = load_qasper(max_papers=N_DOCS)
    pubmed_docs, pubmed_qa = load_pubmedqa(max_papers=N_DOCS)

    datasets = [
        ("squad",    squad_docs,  squad_qa),
        ("pubmedqa", pubmed_docs, pubmed_qa),
    ]

    all_rows, all_summaries = [], []
    for name, docs, qa in datasets:
        rows, summs = run_dataset(name, docs, qa, reranker)
        all_rows.extend(rows)
        all_summaries.extend(summs)

    # ── Save outputs ──────────────────────────────────────────────────────
    per_q_path   = os.path.join(OUTPUT_DIR, "per_query.csv")
    metrics_path = os.path.join(OUTPUT_DIR, "metrics.csv")
    summary_path = os.path.join(OUTPUT_DIR, "summary.md")

    pd.DataFrame(all_rows).to_csv(per_q_path, index=False)
    metrics_df = pd.DataFrame([s for s in all_summaries if s])
    metrics_df.to_csv(metrics_path, index=False)

    # ── Markdown summary ──────────────────────────────────────────────────
    with open(summary_path, "w") as f:
        f.write("# Reranker Experiment — Summary\n\n")
        f.write(f"N_DOCS={N_DOCS}, N_QUESTIONS={N_QUESTIONS}, "
                f"MODEL={MODEL_NAME}, CHUNK={CHUNK_SIZE}, "
                f"TOP_K={TOP_K}, FETCH_K={FETCH_K}\n\n")
        for ds in ["squad", "pubmedqa"]:
            sub = metrics_df[metrics_df["dataset"] == ds]
            if sub.empty:
                continue
            f.write(f"## {ds.upper()}\n\n")
            f.write("| Condition | Faithfulness | Halluc. Rate | Mean CE Score | Latency |\n")
            f.write("|-----------|:----------:|:----------:|:----------:|:------:|\n")
            for _, row in sub.iterrows():
                f.write(
                    f"| {row['condition']} "
                    f"| {row.get('nli_faithfulness', 'n/a')} "
                    f"| {row.get('hallucination_rate', 'n/a')}% "
                    f"| {row.get('mean_reranker_ce', 'n/a')} "
                    f"| {row.get('mean_latency_s', 'n/a')}s |\n"
                )
            f.write("\n")

    print(f"\n[DONE] Results saved to {OUTPUT_DIR}/")
    print(f"       per_query.csv : {len(all_rows)} rows")
    print(f"       metrics.csv   : {len(metrics_df)} rows")
    print(metrics_df[["dataset","condition","nli_faithfulness",
                       "hallucination_rate","mean_latency_s"]].to_string(index=False))


if __name__ == "__main__":
    main()
