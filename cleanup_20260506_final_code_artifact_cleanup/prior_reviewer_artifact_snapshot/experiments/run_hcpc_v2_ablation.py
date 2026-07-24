"""
HCPC-Selective v2 Ablation — Controlled Comparison
====================================================

Compares three conditions on the same datasets, same documents, same queries:
  baseline    — fixed 1024-token chunks, standard cosine retrieval
  hcpc_v1     — original HCPC (sim OR ce threshold, no gating/cap/merge-back)
  hcpc_v2     — HCPC-Selective v2 (AND gate, top-k protection, merge-back, CCS)

All controlled variables are held constant within a dataset run:
  • Documents indexed          (same set, same 1024-token chunks)
  • Queries evaluated          (same ordered list, N_QUESTIONS)
  • LLM model                  (MODEL_NAME)
  • Embedding model            (EMBED_MODEL)
  • top_k                      (TOP_K)
  • Prompt template            (RAGPipeline.RAG_PROMPT)

Outputs (results/hcpc_v2/)
  ├── per_query.csv             one row per query × condition
  ├── metrics.csv               aggregate table: dataset × condition
  ├── summary.md                human-readable result summary
  └── logs/
       ├── <dataset>_baseline_logs.json
       ├── <dataset>_hcpc_v1_logs.json
       ├── <dataset>_hcpc_v2_logs.json
       └── <dataset>_hcpc_v2_diagnostics.json   (full per-query v2 logs)

Run:
    venv/bin/python3 run_hcpc_v2_ablation.py
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from typing import Any

import pandas as pd
from tqdm import tqdm

from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.retrieval_metrics import compute_retrieval_quality
from src.failure_logger import FailureLogger
from src.data_loader import load_qasper
from src.pubmedqa_loader import load_pubmedqa


# ── Experiment parameters ─────────────────────────────────────────────────────
# Identical to run_hcpc_ablation.py for a clean apples-to-apples comparison.

N_DOCS      = 30
N_QUESTIONS = 20
MODEL_NAME  = "mistral"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K       = 3
CHUNK_SIZE  = 1024

# HCPC v1 hyper-parameters (mirrors run_hcpc_ablation.py defaults)
V1_SIM_THRESHOLD  = 0.50
V1_CE_THRESHOLD   = 0.00
V1_SUB_CHUNK_SIZE = 256
V1_SUB_OVERLAP    = 32

# HCPC v2 hyper-parameters
V2_SIM_THRESHOLD   = 0.45
V2_CE_THRESHOLD    = -0.20
V2_TOP_K_PROTECTED = 2
V2_MAX_REFINE      = 2
V2_SUB_CHUNK_SIZE  = 256
V2_SUB_OVERLAP     = 32

OUTPUT_DIR = "results/hcpc_v2"
LOG_DIR    = os.path.join(OUTPUT_DIR, "logs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR,    exist_ok=True)


# ── Baseline run ──────────────────────────────────────────────────────────────

def run_baseline(
    pipeline: RAGPipeline,
    qa_pairs: list[dict],
    detector: HallucinationDetector,
    dataset_name: str,
) -> tuple[list[dict], dict]:
    """Fixed 1024-token chunks, standard cosine retrieval.  No refinement."""
    label    = "baseline"
    log_path = os.path.join(LOG_DIR, f"{dataset_name}_{label}_logs.json")
    fl       = FailureLogger(log_path, log_all=True)
    results: list[dict] = []

    _banner(dataset_name, "FIXED-1024 BASELINE")

    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc=f"{dataset_name}/baseline"):
        try:
            docs, sim_scores = pipeline.retrieve_with_scores(qa["question"])
            gen   = pipeline.generate(qa["question"], docs)
            nli   = detector.detect(gen["answer"], gen["context"])
            ret_m = compute_retrieval_quality(
                qa["question"], docs, pipeline.embeddings
            )
            ret_m["chroma_mean_score"] = (
                round(sum(sim_scores) / len(sim_scores), 4) if sim_scores else 0.0
            )

            record = _build_record(
                dataset=dataset_name,
                condition=label,
                qa=qa,
                gen=gen,
                nli=nli,
                ret_m=ret_m,
                extra={
                    "hcpc_n_strong":              len(docs),
                    "hcpc_n_weak":                0,
                    "hcpc_n_refined":             0,
                    "hcpc_n_merged":              0,
                    "hcpc_context_coherence":     1.0,
                    "hcpc_context_token_count":   sum(
                        len(d.page_content) for d in docs
                    ) // 4,
                },
            )
            results.append(record)

            fl.log(
                query=qa["question"],
                retrieved_context=gen["context"],
                generated_output=gen["answer"],
                faithfulness_score=nli["faithfulness_score"],
                is_hallucination=nli["is_hallucination"],
                sentence_scores=nli.get("sentence_scores", []),
                retrieval_metrics=ret_m,
                metadata={
                    "dataset":      dataset_name,
                    "condition":    label,
                    "chunk_size":   CHUNK_SIZE,
                    "top_k":        TOP_K,
                    "ground_truth": qa.get("ground_truth", ""),
                },
            )
        except Exception as exc:
            print(f"[HCPCv2] Warning ({dataset_name}/baseline): {exc}")

    fl.save()
    fl.to_csv()
    summary = _build_summary(dataset_name, label, results)
    return results, summary


# ── HCPC v1 run ───────────────────────────────────────────────────────────────

def run_hcpc_v1(
    pipeline: RAGPipeline,
    hcpc: HCPCRetriever,
    qa_pairs: list[dict],
    detector: HallucinationDetector,
    dataset_name: str,
) -> tuple[list[dict], dict]:
    """Original HCPC retriever (OR-gate, no gating/cap/merge-back)."""
    label    = "hcpc_v1"
    log_path = os.path.join(LOG_DIR, f"{dataset_name}_{label}_logs.json")
    fl       = FailureLogger(log_path, log_all=True)
    results: list[dict] = []
    all_logs: list[dict] = []

    _banner(dataset_name,
            f"HCPC v1 (sim≥{V1_SIM_THRESHOLD}, ce≥{V1_CE_THRESHOLD})")

    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc=f"{dataset_name}/hcpc_v1"):
        try:
            docs, hlog = hcpc.retrieve(qa["question"])
            all_logs.append(hlog)

            gen   = pipeline.generate(qa["question"], docs)
            nli   = detector.detect(gen["answer"], gen["context"])
            ret_m = compute_retrieval_quality(
                qa["question"], docs, pipeline.embeddings
            )
            ret_m["hcpc_n_weak"]    = hlog["n_weak"]
            ret_m["hcpc_n_refined"] = hlog["n_refined"]

            record = _build_record(
                dataset=dataset_name,
                condition=label,
                qa=qa,
                gen=gen,
                nli=nli,
                ret_m=ret_m,
                extra={
                    "hcpc_n_strong":  hlog["n_strong"],
                    "hcpc_n_weak":    hlog["n_weak"],
                    "hcpc_n_refined": hlog["n_refined"],
                    "hcpc_n_merged":  0,   # v1 has no merge-back
                    "hcpc_mean_ce_improvement": (
                        round(
                            sum(r.get("ce_improvement", 0)
                                for r in hlog["refinements"]) /
                            max(len(hlog["refinements"]), 1),
                            4,
                        ) if hlog["refinements"] else 0.0
                    ),
                    "hcpc_mean_sim_improvement": (
                        round(
                            sum(r.get("sim_improvement", 0)
                                for r in hlog["refinements"]) /
                            max(len(hlog["refinements"]), 1),
                            4,
                        ) if hlog["refinements"] else 0.0
                    ),
                    "hcpc_context_coherence":   -1.0,  # not computed by v1
                    "hcpc_context_token_count": sum(
                        len(d.page_content) for d in docs
                    ) // 4,
                },
            )
            results.append(record)

            fl.log(
                query=qa["question"],
                retrieved_context=gen["context"],
                generated_output=gen["answer"],
                faithfulness_score=nli["faithfulness_score"],
                is_hallucination=nli["is_hallucination"],
                sentence_scores=nli.get("sentence_scores", []),
                retrieval_metrics=ret_m,
                metadata={
                    "dataset":      dataset_name,
                    "condition":    label,
                    "chunk_size":   CHUNK_SIZE,
                    "top_k":        TOP_K,
                    "ground_truth": qa.get("ground_truth", ""),
                    "hcpc_log":     hlog,
                },
            )
        except Exception as exc:
            print(f"[HCPCv2] Warning ({dataset_name}/hcpc_v1): {exc}")

    fl.save()
    fl.to_csv()

    hcpc_stats = hcpc.summary_stats(all_logs)
    summary = _build_summary(dataset_name, label, results)
    summary.update({
        "v1_pct_queries_refined":  hcpc_stats.get("pct_queries_with_refinement", 0.0),
        "v1_mean_ce_improvement":  hcpc_stats.get("mean_ce_improvement", 0.0),
        "v1_mean_sim_improvement": hcpc_stats.get("mean_sim_improvement", 0.0),
        "v1_mean_n_weak":          hcpc_stats.get("mean_n_weak_per_query", 0.0),
    })
    return results, summary


# ── HCPC v2 run ───────────────────────────────────────────────────────────────

def run_hcpc_v2(
    pipeline: RAGPipeline,
    hcpc_v2: HCPCv2Retriever,
    qa_pairs: list[dict],
    detector: HallucinationDetector,
    dataset_name: str,
) -> tuple[list[dict], dict]:
    """HCPC-Selective v2: AND-gate, protection, cap, merge-back, CCS."""
    label    = "hcpc_v2"
    log_path = os.path.join(LOG_DIR, f"{dataset_name}_{label}_logs.json")
    fl       = FailureLogger(log_path, log_all=True)
    results: list[dict] = []
    all_logs: list[dict] = []

    _banner(
        dataset_name,
        f"HCPC v2 (AND gate, sim<{hcpc_v2.sim_threshold}&"
        f"ce<{hcpc_v2.ce_threshold}, "
        f"prot={hcpc_v2.top_k_protected}, cap={hcpc_v2.max_refine})",
    )

    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc=f"{dataset_name}/hcpc_v2"):
        try:
            docs, hlog = hcpc_v2.retrieve(qa["question"])
            all_logs.append(hlog)

            gen   = pipeline.generate(qa["question"], docs)
            nli   = detector.detect(gen["answer"], gen["context"])
            ret_m = compute_retrieval_quality(
                qa["question"], docs, pipeline.embeddings
            )
            # Augment retrieval metrics with v2 diagnostics
            ret_m["hcpc_v2_n_refined"]       = hlog["n_refined_chunks"]
            ret_m["hcpc_v2_n_merged"]        = hlog["n_merged_chunks"]
            ret_m["hcpc_v2_context_coherence"] = hlog["context_coherence"]

            record = _build_record(
                dataset=dataset_name,
                condition=label,
                qa=qa,
                gen=gen,
                nli=nli,
                ret_m=ret_m,
                extra={
                    "hcpc_refined":              hlog["refined"],
                    "hcpc_n_chunks_before":      hlog["n_chunks_before"],
                    "hcpc_n_chunks_after":       hlog["n_chunks_after"],
                    "hcpc_n_refined":            hlog["n_refined_chunks"],
                    "hcpc_n_merged":             hlog["n_merged_chunks"],
                    "hcpc_best_sim_before":      hlog["best_sim_before"],
                    "hcpc_best_sim_after":       hlog["best_sim_after"],
                    "hcpc_best_ce_before":       hlog["best_ce_before"],
                    "hcpc_best_ce_after":        hlog["best_ce_after"],
                    "hcpc_context_coherence":    hlog["context_coherence"],
                    "hcpc_context_token_count":  hlog["context_token_count"],
                },
            )
            results.append(record)

            fl.log(
                query=qa["question"],
                retrieved_context=gen["context"],
                generated_output=gen["answer"],
                faithfulness_score=nli["faithfulness_score"],
                is_hallucination=nli["is_hallucination"],
                sentence_scores=nli.get("sentence_scores", []),
                retrieval_metrics=ret_m,
                metadata={
                    "dataset":      dataset_name,
                    "condition":    label,
                    "chunk_size":   CHUNK_SIZE,
                    "top_k":        TOP_K,
                    "ground_truth": qa.get("ground_truth", ""),
                    "hcpc_v2_log":  hlog,
                },
            )
        except Exception as exc:
            print(f"[HCPCv2] Warning ({dataset_name}/hcpc_v2): {exc}")

    fl.save()
    fl.to_csv()

    # Save full per-query v2 diagnostic logs
    diag_path = os.path.join(LOG_DIR, f"{dataset_name}_hcpc_v2_diagnostics.json")
    with open(diag_path, "w") as fh:
        json.dump(all_logs, fh, indent=2)
    print(f"[HCPCv2] Diagnostics → {diag_path}")

    v2_stats = HCPCv2Retriever.summary_stats(all_logs)
    print(f"[HCPCv2] v2 stats: {v2_stats}")

    summary = _build_summary(dataset_name, label, results)
    summary.update({
        "v2_pct_queries_refined":    v2_stats.get("pct_queries_refined",       0.0),
        "v2_mean_n_refined":         v2_stats.get("mean_n_refined_per_query",  0.0),
        "v2_mean_n_merged":          v2_stats.get("mean_n_merged_per_query",   0.0),
        "v2_mean_context_coherence": v2_stats.get("mean_context_coherence",    0.0),
        "v2_mean_sim_improvement":   v2_stats.get("mean_sim_improvement",      0.0),
        "v2_mean_ce_improvement":    v2_stats.get("mean_ce_improvement",       0.0),
    })
    return results, summary


# ── Comparison tables ─────────────────────────────────────────────────────────

def print_comparison(summaries: list[dict]) -> None:
    df = pd.DataFrame(summaries)
    print("\n" + "=" * 72)
    print("HCPC-SELECTIVE v2 — FINAL COMPARISON")
    print("=" * 72)

    for ds in df["dataset"].unique():
        sub  = df[df["dataset"] == ds].copy()
        base = sub[sub["condition"] == "baseline"]
        v1   = sub[sub["condition"] == "hcpc_v1"]
        v2   = sub[sub["condition"] == "hcpc_v2"]

        if base.empty:
            continue

        b = base.iloc[0]
        print(f"\n  Dataset: {ds.upper()}")
        print(f"  {'Metric':<32} {'Baseline':>10} {'HCPC v1':>10} {'HCPC v2':>10}")
        print(f"  {'-'*66}")

        def _val(df_row, col):
            return df_row.iloc[0][col] if not df_row.empty and col in df_row.columns else float("nan")

        for col, label in [
            ("nli_faithfulness",          "NLI Faithfulness"),
            ("hallucination_rate",        "Hallucination Rate"),
            ("mean_retrieval_similarity", "Mean Retrieval Sim"),
        ]:
            bv = b[col]
            v1v = _val(v1, col)
            v2v = _val(v2, col)
            if col == "hallucination_rate":
                print(f"  {label:<32} {bv:>10.1%} {v1v:>10.1%} {v2v:>10.1%}")
            else:
                print(f"  {label:<32} {bv:>10.4f} {v1v:>10.4f} {v2v:>10.4f}")

        # v2-specific stats
        if not v2.empty:
            r = v2.iloc[0]
            for key, lbl in [
                ("v2_pct_queries_refined",    "Queries Refined (%)"),
                ("v2_mean_context_coherence", "Mean CCS"),
                ("v2_mean_n_merged",          "Mean Chunks Merged"),
                ("v2_mean_sim_improvement",   "Mean Sim Improvement"),
            ]:
                if key in r:
                    val = r[key]
                    if key == "v2_pct_queries_refined":
                        print(f"  {lbl:<32} {'—':>10} {'—':>10} {val:>10.1f}%")
                    else:
                        print(f"  {lbl:<32} {'—':>10} {'—':>10} {val:>10.4f}")


def _build_summary_md(summaries: list[dict]) -> str:
    """Generate summary.md from aggregated results."""
    lines = [
        "# HCPC-Selective v2 — Experiment Summary",
        "",
        "> Generated by `run_hcpc_v2_ablation.py`.",
        "> All faithfulness scores computed by `cross-encoder/nli-deberta-v3-base`.",
        "",
    ]
    df = pd.DataFrame(summaries)
    for ds in df["dataset"].unique():
        sub = df[df["dataset"] == ds]
        lines.append(f"## {ds.upper()}")
        lines.append("")
        lines.append(
            "| condition | faithfulness | halluc_rate | mean_sim | "
            "refined% | CCS | n_merged |"
        )
        lines.append(
            "|-----------|-------------|-------------|----------|"
            "---------|-----|----------|"
        )
        for _, r in sub.iterrows():
            lines.append(
                f"| {r['condition']} "
                f"| {r['nli_faithfulness']:.4f} "
                f"| {r['hallucination_rate']:.1%} "
                f"| {r['mean_retrieval_similarity']:.4f} "
                f"| {r.get('v2_pct_queries_refined', '—')} "
                f"| {r.get('v2_mean_context_coherence', '—')} "
                f"| {r.get('v2_mean_n_merged', '—')} |"
            )
        lines.append("")
    return "\n".join(lines)


# ── Record / summary builders ─────────────────────────────────────────────────

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
) -> dict:
    if not results:
        return {}
    n        = len(results)
    avg_f    = sum(r["faithfulness_score"] for r in results) / n
    halluc   = sum(1 for r in results if r["is_hallucination"]) / n
    avg_sim  = sum(r.get("ret_mean_similarity", 0.0) for r in results) / n
    n_halluc = sum(1 for r in results if r["is_hallucination"])

    s = {
        "dataset":                   dataset,
        "condition":                 condition,
        "chunk_size":                CHUNK_SIZE,
        "top_k":                     TOP_K,
        "n_queries":                 n,
        "n_hallucinated":            n_halluc,
        "nli_faithfulness":          round(avg_f,   4),
        "hallucination_rate":        round(halluc,  4),
        "mean_retrieval_similarity": round(avg_sim, 4),
    }
    print(
        f"[HCPCv2] {dataset}/{condition} → "
        f"faith={s['nli_faithfulness']:.4f}  "
        f"halluc={s['hallucination_rate']:.1%}  "
        f"sim={s['mean_retrieval_similarity']:.4f}"
    )
    return s


def _banner(dataset: str, label: str) -> None:
    print(f"\n{'='*64}")
    print(f"[HCPCv2] {dataset.upper()} | {label}")
    print(f"{'='*64}")


def _get_v2_params(dataset_name: str) -> dict[str, float | int]:
    """Return the tuned HCPC v2 parameters for a dataset."""
    if dataset_name == "squad":
        return {
            "sim_threshold": 0.4,
            "ce_threshold": -0.2,
            "top_k_protected": 2,
        }
    if dataset_name == "pubmedqa":
        return {
            "sim_threshold": 0.6,
            "ce_threshold": -0.2,
            "top_k_protected": 2,
        }
    return {
        "sim_threshold": V2_SIM_THRESHOLD,
        "ce_threshold": V2_CE_THRESHOLD,
        "top_k_protected": V2_TOP_K_PROTECTED,
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("[HCPCv2] Loading datasets...")
    squad_docs,  squad_qa  = load_qasper(max_papers=N_DOCS)
    pubmed_docs, pubmed_qa = load_pubmedqa(max_papers=N_DOCS)

    print("[HCPCv2] Loading hallucination detector...")
    detector = HallucinationDetector()

    all_results:   list[dict] = []
    all_summaries: list[dict] = []

    datasets = [
        ("squad",    squad_docs,  squad_qa),
        ("pubmedqa", pubmed_docs, pubmed_qa),
    ]

    for ds_name, docs, qa in datasets:
        # ── Build ONE shared 1024-token index ──────────────────────────────────
        collection_name = f"hcpc_v2_{ds_name}"
        pipeline = RAGPipeline(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=int(CHUNK_SIZE * 0.1),
            top_k=TOP_K,
            model_name=MODEL_NAME,
            embed_model=EMBED_MODEL,
            persist_dir=f"./chroma_db_hcpc/{collection_name}",
        )
        n_chunks = pipeline.index_documents(docs, collection_name=collection_name)
        print(f"[HCPCv2] {ds_name}: indexed {n_chunks} chunks (1024-token fixed)")

        # ── Condition 1: Baseline ─────────────────────────────────────────────
        base_results, base_summary = run_baseline(pipeline, qa, detector, ds_name)
        all_results.extend(base_results)
        if base_summary:
            base_summary["n_chunks_indexed"] = n_chunks
            all_summaries.append(base_summary)

        # ── Condition 2: HCPC v1 (original, for direct comparison) ───────────
        # Initialised once per dataset; same cross-encoder will be reused by v2
        hcpc_v1 = HCPCRetriever(
            pipeline=pipeline,
            sim_threshold=V1_SIM_THRESHOLD,
            ce_threshold=V1_CE_THRESHOLD,
            sub_chunk_size=V1_SUB_CHUNK_SIZE,
            sub_chunk_overlap=V1_SUB_OVERLAP,
            top_k=TOP_K,
        )
        v1_results, v1_summary = run_hcpc_v1(
            pipeline, hcpc_v1, qa, detector, ds_name
        )
        all_results.extend(v1_results)
        if v1_summary:
            v1_summary["n_chunks_indexed"] = n_chunks
            all_summaries.append(v1_summary)

        # ── Condition 3: HCPC v2 ─────────────────────────────────────────────
        v2_params = _get_v2_params(ds_name)
        hcpc_v2 = HCPCv2Retriever(
            pipeline=pipeline,
            sim_threshold=v2_params["sim_threshold"],
            ce_threshold=v2_params["ce_threshold"],
            top_k_protected=v2_params["top_k_protected"],
            max_refine=V2_MAX_REFINE,
            sub_chunk_size=V2_SUB_CHUNK_SIZE,
            sub_chunk_overlap=V2_SUB_OVERLAP,
        )
        v2_results, v2_summary = run_hcpc_v2(
            pipeline, hcpc_v2, qa, detector, ds_name
        )
        all_results.extend(v2_results)
        if v2_summary:
            v2_summary["n_chunks_indexed"] = n_chunks
            all_summaries.append(v2_summary)

        # Per-dataset CSVs (crash-safe)
        if base_results:
            pd.DataFrame(base_results).to_csv(
                os.path.join(OUTPUT_DIR, f"{ds_name}_baseline.csv"), index=False
            )
        if v1_results:
            pd.DataFrame(v1_results).to_csv(
                os.path.join(OUTPUT_DIR, f"{ds_name}_hcpc_v1.csv"), index=False
            )
        if v2_results:
            pd.DataFrame(v2_results).to_csv(
                os.path.join(OUTPUT_DIR, f"{ds_name}_hcpc_v2.csv"), index=False
            )

    # ── Consolidated outputs ──────────────────────────────────────────────────
    if all_results:
        pd.DataFrame(all_results).to_csv(
            os.path.join(OUTPUT_DIR, "per_query.csv"), index=False
        )
        print(f"[HCPCv2] per_query.csv → {OUTPUT_DIR}/per_query.csv")

    if all_summaries:
        metrics_df = pd.DataFrame(all_summaries)
        metrics_df.to_csv(
            os.path.join(OUTPUT_DIR, "metrics.csv"), index=False
        )
        with open(os.path.join(OUTPUT_DIR, "metrics.json"), "w") as fh:
            json.dump(all_summaries, fh, indent=2)

        md_text = _build_summary_md(all_summaries)
        with open(os.path.join(OUTPUT_DIR, "summary.md"), "w") as fh:
            fh.write(md_text)

        print(f"[HCPCv2] metrics.csv  → {OUTPUT_DIR}/metrics.csv")
        print(f"[HCPCv2] summary.md   → {OUTPUT_DIR}/summary.md")

    if all_summaries:
        print_comparison(all_summaries)

    print(f"\n[HCPCv2] All outputs written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
