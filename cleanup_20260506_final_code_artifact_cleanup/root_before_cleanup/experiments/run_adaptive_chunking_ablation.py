"""
Adaptive Chunking Ablation Study
=================================
Compares three chunking strategies on SQuAD and PubMedQA:

  fixed    — RecursiveCharacterTextSplitter (baseline, existing approach)
  semantic — SemanticChunker: groups sentences by embedding cosine similarity
  dynamic  — DynamicChunker: respects paragraph structure, merges/splits as needed

For each strategy, records:
  - NLI faithfulness score
  - Hallucination rate
  - Retrieval quality metrics (mean/max/min cosine similarity, relevance spread)
  - Chunk count and mean chunk length

Results are stored in:
  results/adaptive/
    summary.csv            — aggregate metrics per strategy × dataset
    summary.json           — same in JSON
    squad_fixed.csv        — per-query results for SQuAD fixed
    squad_semantic_*.csv   — per-query results for SQuAD semantic (one per threshold)
    squad_dynamic.csv      — per-query results for SQuAD dynamic
    pubmedqa_*.csv         — same for PubMedQA
    logs/
      squad_fixed_logs.json      — full FailureLogger JSON (all queries)
      squad_semantic_*_logs.json
      ...

Run:
    python run_adaptive_chunking_ablation.py

To limit scope during development, set N_QUESTIONS and N_DOCS at the top.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd
from tqdm import tqdm

from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.adaptive_chunker import SemanticChunker, DynamicChunker, get_chunker
from src.retrieval_metrics import compute_retrieval_quality
from src.failure_logger import FailureLogger
from src.data_loader import load_qasper
from src.pubmedqa_loader import load_pubmedqa


# ── Experiment parameters ─────────────────────────────────────────────────────

N_DOCS = 30          # number of source documents to index per run
N_QUESTIONS = 30     # queries evaluated per configuration
MODEL_NAME = "mistral"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

OUTPUT_DIR = "results/adaptive"
LOG_DIR = os.path.join(OUTPUT_DIR, "logs")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


# ── Strategy definitions ──────────────────────────────────────────────────────
#
# Each entry describes one chunking configuration.
# The "chunker_kwargs" will be resolved later once embeddings are available.
#
# Format:
#   name         : short identifier used in output file names
#   strategy     : "fixed" | "semantic" | "dynamic"
#   chunk_size   : used only for fixed strategy (and for the RAGPipeline default)
#   chunker_kwargs : passed to get_chunker() (not used for fixed)
#   top_k        : retrieval depth
#   description  : human-readable label for summary tables

STRATEGY_CONFIGS: list[dict] = [
    {
        "name": "fixed_256",
        "strategy": "fixed",
        "chunk_size": 256,
        "top_k": 3,
        "description": "Fixed 256-token chunks (baseline)",
    },
    {
        "name": "fixed_512",
        "strategy": "fixed",
        "chunk_size": 512,
        "top_k": 3,
        "description": "Fixed 512-token chunks (baseline)",
    },
    {
        "name": "fixed_1024",
        "strategy": "fixed",
        "chunk_size": 1024,
        "top_k": 3,
        "description": "Fixed 1024-token chunks (baseline)",
    },
    {
        "name": "semantic_tight",
        "strategy": "semantic",
        "chunk_size": 512,   # used only as fallback in RAGPipeline
        "top_k": 3,
        "chunker_kwargs": {
            "similarity_threshold": 0.6,
            "max_chunk_chars": 2400,
            "min_chunk_chars": 200,
        },
        "description": "Semantic chunking (threshold=0.6, tight cohesion)",
    },
    {
        "name": "semantic_loose",
        "strategy": "semantic",
        "chunk_size": 512,
        "top_k": 3,
        "chunker_kwargs": {
            "similarity_threshold": 0.4,
            "max_chunk_chars": 3200,
            "min_chunk_chars": 200,
        },
        "description": "Semantic chunking (threshold=0.4, loose cohesion)",
    },
    {
        "name": "dynamic",
        "strategy": "dynamic",
        "chunk_size": 512,
        "top_k": 3,
        "chunker_kwargs": {
            "min_chunk_chars": 300,
            "max_chunk_chars": 3000,
            "overlap_chars": 100,
        },
        "description": "Dynamic paragraph-aware chunking",
    },
]


# ── Core experiment function ──────────────────────────────────────────────────

def run_config(
    config: dict,
    documents: list,
    qa_pairs: list,
    detector: HallucinationDetector,
    dataset_name: str,
    embeddings_ref: Any,                # shared embeddings object from first pipeline
    collection_suffix: int,
) -> tuple[list[dict], dict]:
    """
    Run one chunking strategy configuration and return (per_query_results, summary).
    """
    name = config["name"]
    strategy = config["strategy"]
    chunk_size = config.get("chunk_size", 512)
    top_k = config.get("top_k", 3)
    chunker_kwargs = config.get("chunker_kwargs", {})

    print(f"\n{'='*64}")
    print(f"[Adaptive] {dataset_name.upper()} | {name} | {config['description']}")
    print(f"{'='*64}")

    # Build chunker
    if strategy == "fixed":
        chunker = None  # RAGPipeline uses its own text_splitter
    elif strategy == "semantic":
        chunker = SemanticChunker(embeddings=embeddings_ref, **chunker_kwargs)
    elif strategy == "dynamic":
        chunker = DynamicChunker(**chunker_kwargs)
    else:
        raise ValueError(f"Unknown strategy: {strategy!r}")

    # Build pipeline (reuse the persist_dir so ChromaDB collections are separate)
    collection_name = f"{dataset_name}_{name}_{collection_suffix}"
    pipeline = RAGPipeline(
        chunk_size=chunk_size,
        chunk_overlap=int(chunk_size * 0.1),
        top_k=top_k,
        model_name=MODEL_NAME,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_adaptive/{collection_name}",
        chunker=chunker,
    )

    n_chunks = pipeline.index_documents(documents, collection_name=collection_name)
    mean_chunk_len = _estimate_mean_chunk_len(documents, chunker, chunk_size)

    # Set up failure logger
    log_path = os.path.join(LOG_DIR, f"{dataset_name}_{name}_logs.json")
    logger = FailureLogger(log_path, log_all=True)

    results: list[dict] = []

    for qa in tqdm(qa_pairs[:N_QUESTIONS], desc=f"{name}"):
        try:
            docs, sim_scores = pipeline.retrieve_with_scores(qa["question"])
            gen_result = pipeline.generate(qa["question"], docs)
            nli = detector.detect(gen_result["answer"], gen_result["context"])

            # Retrieval quality metrics (use the shared embeddings object)
            ret_metrics = compute_retrieval_quality(
                query=qa["question"],
                docs=docs,
                embeddings=pipeline.embeddings,
            )
            # Also store the ChromaDB similarity scores
            ret_metrics["chroma_mean_score"] = (
                round(sum(sim_scores) / len(sim_scores), 4) if sim_scores else 0.0
            )

            record: dict = {
                "dataset": dataset_name,
                "chunking_strategy": name,
                "strategy_type": strategy,
                "chunk_size_param": chunk_size,
                "top_k": top_k,
                "question": qa["question"],
                "ground_truth": qa.get("ground_truth", ""),
                "answer": gen_result["answer"],
                "faithfulness_score": nli["faithfulness_score"],
                "is_hallucination": nli["is_hallucination"],
                "nli_label": nli["label"],
                "latency_s": gen_result["latency_s"],
                **{f"ret_{k}": v for k, v in ret_metrics.items()},
            }
            results.append(record)

            logger.log(
                query=qa["question"],
                retrieved_context=gen_result["context"],
                generated_output=gen_result["answer"],
                faithfulness_score=nli["faithfulness_score"],
                is_hallucination=nli["is_hallucination"],
                sentence_scores=nli.get("sentence_scores", []),
                retrieval_metrics=ret_metrics,
                metadata={
                    "dataset": dataset_name,
                    "chunking_strategy": name,
                    "strategy_type": strategy,
                    "chunk_size_param": chunk_size,
                    "top_k": top_k,
                    "ground_truth": qa.get("ground_truth", ""),
                },
            )

        except Exception as exc:
            print(f"[Adaptive] Warning: query failed — {exc}")
            continue

    logger.save()
    logger.to_csv()

    if not results:
        return results, {}

    avg_faith = sum(r["faithfulness_score"] for r in results) / len(results)
    halluc_rate = sum(1 for r in results if r["is_hallucination"]) / len(results)
    avg_sim = sum(r.get("ret_mean_similarity", 0.0) for r in results) / len(results)

    summary: dict = {
        "dataset": dataset_name,
        "chunking_strategy": name,
        "strategy_type": strategy,
        "description": config["description"],
        "chunk_size_param": chunk_size,
        "top_k": top_k,
        "n_chunks_indexed": n_chunks,
        "mean_chunk_len_chars": mean_chunk_len,
        "n_queries": len(results),
        "nli_faithfulness": round(avg_faith, 4),
        "hallucination_rate": round(halluc_rate, 4),
        "mean_retrieval_similarity": round(avg_sim, 4),
        "n_hallucinated": sum(1 for r in results if r["is_hallucination"]),
    }

    print(
        f"[Adaptive] Done → faithfulness={summary['nli_faithfulness']:.4f}  "
        f"halluc={summary['hallucination_rate']:.1%}  "
        f"sim={summary['mean_retrieval_similarity']:.4f}"
    )
    return results, summary


# ── Utility ───────────────────────────────────────────────────────────────────

def _estimate_mean_chunk_len(documents: list, chunker: Any, chunk_size: int) -> int:
    """Estimate mean chunk character length without re-embedding."""
    try:
        if chunker is None:
            # Fixed: approximate from chunk_size (4 chars/token rough estimate)
            return chunk_size * 4
        elif hasattr(chunker, "STRATEGY") and chunker.STRATEGY == "semantic":
            # We already chunked during index_documents; estimate from docs
            total = sum(len(d.page_content) for d in documents)
            # Rough: semantic threshold ~ 0.5 groups ~3-8 sentences per chunk
            return max(200, total // max(len(documents) * 3, 1))
        else:
            # Dynamic: re-chunk a small sample to measure
            sample = documents[:min(3, len(documents))]
            chunks = chunker.split_documents(sample)
            if chunks:
                return int(sum(len(c.page_content) for c in chunks) / len(chunks))
    except Exception:
        pass
    return -1


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("[Adaptive] Loading datasets...")
    squad_docs, squad_qa = load_qasper(max_papers=N_DOCS)
    pubmed_docs, pubmed_qa = load_pubmedqa(max_papers=N_DOCS)

    print("[Adaptive] Loading hallucination detector...")
    detector = HallucinationDetector()

    # Bootstrap one pipeline just to get the shared embeddings object.
    # All subsequent pipelines will use the same embed_model so sharing
    # is safe; this avoids loading the same 80 MB model repeatedly.
    print("[Adaptive] Initialising shared embeddings...")
    _seed_pipeline = RAGPipeline(
        model_name=MODEL_NAME,
        embed_model=EMBED_MODEL,
        persist_dir="./chroma_db_adaptive/seed",
    )
    shared_emb = _seed_pipeline.embeddings

    all_results: list[dict] = []
    all_summaries: list[dict] = []

    datasets = [
        ("squad", squad_docs, squad_qa),
        ("pubmedqa", pubmed_docs, pubmed_qa),
    ]

    for ds_name, docs, qa in datasets:
        for idx, cfg in enumerate(STRATEGY_CONFIGS):
            per_query, summary = run_config(
                config=cfg,
                documents=docs,
                qa_pairs=qa,
                detector=detector,
                dataset_name=ds_name,
                embeddings_ref=shared_emb,
                collection_suffix=idx,
            )
            all_results.extend(per_query)
            if summary:
                all_summaries.append(summary)

            # Save per-config CSV immediately (safe even if run is interrupted)
            if per_query:
                out_csv = os.path.join(OUTPUT_DIR, f"{ds_name}_{cfg['name']}.csv")
                pd.DataFrame(per_query).to_csv(out_csv, index=False)
                print(f"[Adaptive] Saved → {out_csv}")

    # ── Summary table ─────────────────────────────────────────────────────────
    if all_summaries:
        summary_df = pd.DataFrame(all_summaries).sort_values(
            ["dataset", "nli_faithfulness"], ascending=[True, False]
        )
        summary_df.to_csv(os.path.join(OUTPUT_DIR, "summary.csv"), index=False)
        with open(os.path.join(OUTPUT_DIR, "summary.json"), "w") as fh:
            json.dump(all_summaries, fh, indent=2)

        print("\n" + "="*64)
        print("ADAPTIVE CHUNKING ABLATION — FINAL SUMMARY")
        print("="*64)
        cols = [
            "dataset", "chunking_strategy", "nli_faithfulness",
            "hallucination_rate", "mean_retrieval_similarity",
            "n_chunks_indexed", "mean_chunk_len_chars",
        ]
        print(summary_df[cols].to_string(index=False))

    # ── Comparison table: adaptive vs. best fixed per dataset ─────────────────
    if all_summaries:
        _print_comparison_table(all_summaries)

    print(f"\n[Adaptive] All results written to {OUTPUT_DIR}/")


def _print_comparison_table(summaries: list[dict]) -> None:
    """Print a compact table highlighting adaptive gains over best fixed baseline."""
    df = pd.DataFrame(summaries)

    print("\n" + "-"*64)
    print("ADAPTIVE vs FIXED BASELINE COMPARISON")
    print("-"*64)

    for ds in df["dataset"].unique():
        sub = df[df["dataset"] == ds].copy()
        fixed = sub[sub["strategy_type"] == "fixed"]
        adaptive = sub[sub["strategy_type"].isin(["semantic", "dynamic"])]

        if fixed.empty or adaptive.empty:
            continue

        best_fixed = fixed.loc[fixed["nli_faithfulness"].idxmax()]
        print(f"\n  Dataset: {ds.upper()}")
        print(
            f"  Best fixed  ({best_fixed['chunking_strategy']:15s}): "
            f"faithfulness={best_fixed['nli_faithfulness']:.4f}  "
            f"halluc={best_fixed['hallucination_rate']:.1%}"
        )
        for _, row in adaptive.iterrows():
            delta_f = row["nli_faithfulness"] - best_fixed["nli_faithfulness"]
            delta_h = row["hallucination_rate"] - best_fixed["hallucination_rate"]
            sign_f = "+" if delta_f >= 0 else ""
            sign_h = "+" if delta_h >= 0 else ""
            print(
                f"  {row['chunking_strategy']:20s}: "
                f"faithfulness={row['nli_faithfulness']:.4f} ({sign_f}{delta_f:.4f})  "
                f"halluc={row['hallucination_rate']:.1%} ({sign_h}{delta_h:.1%})"
            )

    comparison_path = os.path.join(OUTPUT_DIR, "adaptive_vs_fixed_comparison.csv")
    df.to_csv(comparison_path, index=False)
    print(f"\n[Adaptive] Comparison table → {comparison_path}")


if __name__ == "__main__":
    main()
