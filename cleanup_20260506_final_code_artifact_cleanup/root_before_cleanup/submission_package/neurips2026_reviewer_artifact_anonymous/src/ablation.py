"""
Ablation Study Runner
Tests combinations of: chunk_size × top_k × prompt_strategy
"""

import json
import os
import pandas as pd
from itertools import product
from tqdm import tqdm

from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.data_loader import load_qasper
from src.evaluator import evaluate_rag, save_results


# ── Ablation Config ───────────────────────────────────────────────────────────

ABLATION_CONFIG = {
    "chunk_sizes": [256, 512, 1024],
    "top_ks": [3, 5],
    "prompt_strategies": ["strict", "cot"],   # strict = default, cot = chain-of-thought
}

COT_PROMPT_TEMPLATE = """You are a careful scientific assistant. Think step by step before answering.

Context from scientific paper:
{context}

Question: {question}

Let's think step by step:
1. What relevant information is in the context?
2. How does it answer the question?

Final Answer:"""


# ── Single Experiment ─────────────────────────────────────────────────────────

def run_experiment(
    documents,
    qa_pairs,
    chunk_size: int,
    top_k: int,
    prompt_strategy: str,
    detector: HallucinationDetector,
    n_questions: int = 30,
    run_id: str = ""
) -> dict:
    """Run one ablation configuration."""
    print(f"\n{'='*60}")
    print(f"[Ablation] chunk_size={chunk_size} | top_k={top_k} | prompt={prompt_strategy}")
    print(f"{'='*60}")

    # Build RAG pipeline with this config
    pipeline = RAGPipeline(
        chunk_size=chunk_size,
        chunk_overlap=int(chunk_size * 0.1),
        top_k=top_k
    )
    pipeline.index_documents(documents, collection_name=f"qasper_{run_id}")

    # Swap prompt if chain-of-thought
    if prompt_strategy == "cot":
        from langchain_core.prompts import PromptTemplate
        pipeline.llm_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=COT_PROMPT_TEMPLATE
        )

    results = []
    sample_qas = qa_pairs[:n_questions]

    for qa in tqdm(sample_qas, desc=f"Querying (chunk={chunk_size}, k={top_k}, {prompt_strategy})"):
        try:
            result = pipeline.query(qa["question"])
            nli_result = detector.detect(result["answer"], result["context"])

            results.append({
                **result,
                "ground_truth": qa["ground_truth"],
                "faithfulness_score": nli_result["faithfulness_score"],
                "is_hallucination": nli_result["is_hallucination"],
                "nli_label": nli_result["label"],
                "chunk_size": chunk_size,
                "top_k": top_k,
                "prompt_strategy": prompt_strategy,
            })
        except Exception as e:
            print(f"[Ablation] Warning: query failed: {e}")
            continue

    # Compute hallucination rate manually (RAGAS needs API, do quick version)
    hallucination_rate = sum(1 for r in results if r["is_hallucination"]) / len(results)
    avg_faithfulness = sum(r["faithfulness_score"] for r in results) / len(results)

    scores = {
        "chunk_size": chunk_size,
        "top_k": top_k,
        "prompt_strategy": prompt_strategy,
        "nli_faithfulness": round(avg_faithfulness, 4),
        "hallucination_rate": round(hallucination_rate, 4),
        "n_samples": len(results),
    }

    # Save this run
    os.makedirs("results", exist_ok=True)
    save_results(
        results,
        scores,
        path=f"results/ablation_chunk{chunk_size}_k{top_k}_{prompt_strategy}.csv"
    )

    return scores


# ── Full Ablation ─────────────────────────────────────────────────────────────

def run_full_ablation(n_papers: int = 30, n_questions: int = 30):
    """Run all ablation combinations and save summary."""

    print("[Ablation] Loading dataset...")
    documents, qa_pairs = load_qasper(max_papers=n_papers)

    print("[Ablation] Loading hallucination detector...")
    detector = HallucinationDetector()

    all_scores = []
    configs = list(product(
        ABLATION_CONFIG["chunk_sizes"],
        ABLATION_CONFIG["top_ks"],
        ABLATION_CONFIG["prompt_strategies"]
    ))

    print(f"[Ablation] Running {len(configs)} configurations × {n_questions} questions each")

    for i, (chunk_size, top_k, prompt_strategy) in enumerate(configs):
        run_id = f"run{i}_{chunk_size}_{top_k}_{prompt_strategy}"
        scores = run_experiment(
            documents=documents,
            qa_pairs=qa_pairs,
            chunk_size=chunk_size,
            top_k=top_k,
            prompt_strategy=prompt_strategy,
            detector=detector,
            n_questions=n_questions,
            run_id=run_id
        )
        all_scores.append(scores)
        print(f"[Ablation] Config {i+1}/{len(configs)} done: {scores}")

    # Save summary table
    summary_df = pd.DataFrame(all_scores)
    summary_df = summary_df.sort_values("nli_faithfulness", ascending=False)
    summary_df.to_csv("results/ablation_summary.csv", index=False)

    print("\n[Ablation] ===== FINAL SUMMARY =====")
    print(summary_df.to_string(index=False))

    # Save as JSON too
    with open("results/ablation_summary.json", "w") as f:
        json.dump(all_scores, f, indent=2)

    return summary_df


if __name__ == "__main__":
    run_full_ablation(n_papers=30, n_questions=30)
