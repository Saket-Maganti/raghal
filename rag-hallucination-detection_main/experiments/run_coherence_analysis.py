"""
run_coherence_analysis.py — "Why Coherence Matters" Analysis
=============================================================

Computes four coherence metrics on every retrieved context across the
baseline, HCPC-v1, and HCPC-v2 conditions and correlates them with
faithfulness scores.

Metrics computed (per query)
-----------------------------
  ccs                 — mean cosine sim between adjacent chunks (= CCS)
  semantic_continuity — alias for CCS (cross-check)
  embedding_variance  — variance of all pairwise inter-chunk cosine sims
  mean_jaccard        — mean token-overlap between adjacent chunks (lexical)
  retrieval_entropy   — Shannon entropy of query-to-chunk similarity distribution
  mean_query_chunk_sim — mean cosine(query, chunk) across retrieved passages
  sim_spread          — max - min query-chunk similarity

Then computes Spearman ρ between each metric and faithfulness_score and
saves a correlation table.

Conditions compared
-------------------
  baseline    — fixed 1024-token chunks, no refinement
  hcpc_v2     — HCPC-Selective v2 (AND-gate + top-2 lock + merge-back)

Outputs (results/coherence_analysis/)
  ├── per_query_metrics.csv     all metrics per query × condition
  ├── correlations.csv          Spearman ρ vs. faithfulness for each metric
  ├── condition_summary.csv     mean metrics per dataset × condition
  └── summary.md                human-readable results

Run
---
    python3 run_coherence_analysis.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from __future__ import annotations

import json
import os
from typing import Dict, List

import pandas as pd
from tqdm import tqdm

from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.retrieval_metrics import compute_retrieval_quality
from src.coherence_metrics import compute_coherence_metrics, correlations_with_faithfulness
from src.data_loader import load_qasper
from src.pubmedqa_loader import load_pubmedqa

# ── Parameters ────────────────────────────────────────────────────────────────

N_DOCS      = 30
N_QUESTIONS = 30
MODEL_NAME  = "llama3"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K       = 3
CHUNK_SIZE  = 1024

V2_SIM_THRESHOLD   = 0.45
V2_CE_THRESHOLD    = -0.20
V2_TOP_K_PROTECTED = 2
V2_MAX_REFINE      = 2

OUTPUT_DIR = "results/coherence_analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Run helpers ───────────────────────────────────────────────────────────────

METRIC_KEYS = [
    "ccs",
    "semantic_continuity",
    "embedding_variance",
    "mean_jaccard",
    "retrieval_entropy",
    "mean_query_chunk_sim",
    "sim_spread",
]


def run_baseline_with_coherence(pipeline, qa_pairs, detector, dataset_name):
    rows = []
    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc=f"{dataset_name}/baseline"):
        try:
            docs, _  = pipeline.retrieve_with_scores(qa["question"])
            gen       = pipeline.generate(qa["question"], docs)
            nli       = detector.detect(gen["answer"], gen["context"])
            coh_m     = compute_coherence_metrics(qa["question"], docs,
                                                  pipeline.embeddings)
            retm      = compute_retrieval_quality(qa["question"], docs,
                                                  pipeline.embeddings)
            row = {
                "dataset":           dataset_name,
                "condition":         "baseline",
                "question":          qa["question"],
                "faithfulness_score": nli["faithfulness_score"],
                "is_hallucination":  nli["is_hallucination"],
                "ret_mean_sim":      retm.get("mean_similarity", -1.0),
                "ret_spread":        retm.get("relevance_spread", -1.0),
            }
            row.update({k: coh_m.get(k, -1.0) for k in METRIC_KEYS})
            rows.append(row)
        except Exception as e:
            print(f"  [WARN] baseline coherence query failed: {e}")
    return rows


def run_hcpc_v2_with_coherence(pipeline, qa_pairs, detector, dataset_name):
    hcpc = HCPCv2Retriever(
        pipeline,
        sim_threshold=V2_SIM_THRESHOLD,
        ce_threshold=V2_CE_THRESHOLD,
        top_k_protected=V2_TOP_K_PROTECTED,
        max_refine=V2_MAX_REFINE,
    )
    rows = []
    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc=f"{dataset_name}/hcpc_v2"):
        try:
            docs, hlog = hcpc.retrieve(qa["question"])
            gen         = pipeline.generate(qa["question"], docs)
            nli         = detector.detect(gen["answer"], gen["context"])
            coh_m       = compute_coherence_metrics(qa["question"], docs,
                                                    pipeline.embeddings)
            retm        = compute_retrieval_quality(qa["question"], docs,
                                                    pipeline.embeddings)
            row = {
                "dataset":           dataset_name,
                "condition":         "hcpc_v2",
                "question":          qa["question"],
                "faithfulness_score": nli["faithfulness_score"],
                "is_hallucination":  nli["is_hallucination"],
                "ret_mean_sim":      retm.get("mean_similarity", -1.0),
                "ret_spread":        retm.get("relevance_spread", -1.0),
                "hcpc_refined":      hlog.get("refined", False),
                "hcpc_n_refined":    hlog.get("n_refined_chunks", 0),
                "hcpc_ccs":          hlog.get("context_coherence", -1.0),
            }
            row.update({k: coh_m.get(k, -1.0) for k in METRIC_KEYS})
            rows.append(row)
        except Exception as e:
            print(f"  [WARN] hcpc_v2 coherence query failed: {e}")
    return rows


def run_dataset(dataset_name, docs_raw, qa_pairs):
    print(f"\n{'='*60}")
    print(f"  Coherence Analysis — {dataset_name.upper()}")
    print(f"{'='*60}")

    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=0,
        top_k=TOP_K,
        model_name=MODEL_NAME,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_coh_{dataset_name}",
    )
    pipeline.index_documents(docs_raw[:N_DOCS],
                              collection_name=f"coh_{dataset_name}")
    detector = HallucinationDetector()

    rows_base = run_baseline_with_coherence(pipeline, qa_pairs, detector, dataset_name)
    rows_v2   = run_hcpc_v2_with_coherence(pipeline, qa_pairs, detector, dataset_name)
    return rows_base + rows_v2


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("[INFO] Loading datasets ...")
    # max_papers caps the document pool; QA pairs are sliced to N_QUESTIONS inside each run.
    squad_docs,  squad_qa  = load_qasper(max_papers=N_DOCS)
    pubmed_docs, pubmed_qa = load_pubmedqa(max_papers=N_DOCS)

    all_rows = []
    for ds_name, docs, qa in [("squad",    squad_docs,  squad_qa),
                               ("pubmedqa", pubmed_docs, pubmed_qa)]:
        all_rows.extend(run_dataset(ds_name, docs, qa))

    df = pd.DataFrame(all_rows)

    # ── Save per-query metrics ────────────────────────────────────────────
    pq_path = os.path.join(OUTPUT_DIR, "per_query_metrics.csv")
    df.to_csv(pq_path, index=False)
    print(f"\n[INFO] Saved per_query_metrics.csv ({len(df)} rows)")

    # ── Spearman correlations ─────────────────────────────────────────────
    corr_rows = []
    for ds, ds_grp in df.groupby("dataset"):
        for cond, cond_grp in ds_grp.groupby("condition"):
            records = cond_grp.to_dict("records")
            corrs = correlations_with_faithfulness(records, METRIC_KEYS)
            for metric, stats in corrs.items():
                corr_rows.append({
                    "dataset":      ds,
                    "condition":    cond,
                    "metric":       metric,
                    "spearman_rho": stats.get("spearman_rho"),
                    "p_value":      stats.get("p_value"),
                    "n":            stats.get("n"),
                })

    corr_df = pd.DataFrame(corr_rows)
    corr_df.to_csv(os.path.join(OUTPUT_DIR, "correlations.csv"), index=False)

    # ── Condition summary (mean metrics) ──────────────────────────────────
    numeric_cols = ["faithfulness_score", "is_hallucination"] + METRIC_KEYS
    numeric_cols = [c for c in numeric_cols if c in df.columns]
    cond_summary = (
        df.groupby(["dataset", "condition"])[numeric_cols]
        .mean()
        .round(4)
        .reset_index()
    )
    cond_summary["hallucination_rate_%"] = (cond_summary["is_hallucination"] * 100).round(1)
    cond_summary.to_csv(os.path.join(OUTPUT_DIR, "condition_summary.csv"), index=False)

    # ── Markdown summary ──────────────────────────────────────────────────
    with open(os.path.join(OUTPUT_DIR, "summary.md"), "w") as f:
        f.write("# Coherence Analysis — \"Why Coherence Matters\"\n\n")
        f.write(f"N_DOCS={N_DOCS}, N_QUESTIONS={N_QUESTIONS}, "
                f"MODEL={MODEL_NAME}, CHUNK={CHUNK_SIZE}, TOP_K={TOP_K}\n\n")
        f.write("## Spearman ρ between coherence metrics and faithfulness\n\n")
        f.write("| Dataset | Condition | Metric | ρ | p-value | n |\n")
        f.write("|---------|-----------|--------|:-:|:-------:|:-:|\n")
        for _, row in corr_df.sort_values(
            ["dataset", "condition", "spearman_rho"],
            ascending=[True, True, False]
        ).iterrows():
            rho_str = f"{row['spearman_rho']:.3f}" if row["spearman_rho"] is not None else "n/a"
            p_str   = f"{row['p_value']:.3f}" if row["p_value"] is not None else "n/a"
            f.write(
                f"| {row['dataset']} | {row['condition']} | {row['metric']} "
                f"| {rho_str} | {p_str} | {row['n']} |\n"
            )

        f.write("\n## Condition means by dataset\n\n")
        for ds in ["squad", "pubmedqa"]:
            sub = cond_summary[cond_summary["dataset"] == ds]
            if sub.empty:
                continue
            f.write(f"### {ds.upper()}\n\n")
            f.write("| Condition | Faithfulness | Halluc.% | CCS | Embed Var | Jaccard | Entropy |\n")
            f.write("|-----------|:----------:|:------:|:---:|:--------:|:-------:|:-------:|\n")
            for _, row in sub.iterrows():
                f.write(
                    f"| {row['condition']} "
                    f"| {row.get('faithfulness_score', 'n/a'):.4f} "
                    f"| {row.get('hallucination_rate_%', 'n/a'):.1f} "
                    f"| {row.get('ccs', 'n/a'):.4f} "
                    f"| {row.get('embedding_variance', 'n/a'):.4f} "
                    f"| {row.get('mean_jaccard', 'n/a'):.4f} "
                    f"| {row.get('retrieval_entropy', 'n/a'):.4f} |\n"
                )
            f.write("\n")

    # ── Print summary ─────────────────────────────────────────────────────
    print("\n[DONE] Results saved to", OUTPUT_DIR)
    print("\nTop correlations with faithfulness (|ρ| > 0.3):\n")
    sig = corr_df[corr_df["spearman_rho"].abs() > 0.3].sort_values(
        "spearman_rho", ascending=False
    )
    if not sig.empty:
        print(sig[["dataset", "condition", "metric", "spearman_rho", "p_value"]].to_string(index=False))
    else:
        print("  (none above 0.3 — check per-dataset breakdown in correlations.csv)")

    print("\nCondition means:")
    display_cols = ["dataset", "condition", "faithfulness_score",
                    "hallucination_rate_%", "ccs", "embedding_variance",
                    "mean_jaccard", "retrieval_entropy"]
    display_cols = [c for c in display_cols if c in cond_summary.columns]
    print(cond_summary[display_cols].to_string(index=False))


if __name__ == "__main__":
    main()
