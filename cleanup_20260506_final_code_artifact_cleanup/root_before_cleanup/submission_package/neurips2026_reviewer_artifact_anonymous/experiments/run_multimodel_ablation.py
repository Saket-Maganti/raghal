"""
Multi-model ablation - RESUME VERSION
Skips already completed configs, starts from Llama-3.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import os
import json
import pandas as pd
from itertools import product
from tqdm import tqdm

from src.data_loader import load_qasper as load_squad
from src.pubmedqa_loader import load_pubmedqa
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector

MODELS   = ["mistral", "llama3"]
DATASETS = ["squad", "pubmedqa"]
CHUNKS   = [256, 512, 1024]
TOPKS    = [3, 5]
PROMPTS  = ["strict", "cot"]
N_PAPERS = 50
N_QUESTIONS = 100

os.makedirs("results/multimodel", exist_ok=True)

# ── Load completed configs ────────────────────────────────────────────────────
completed = set()
summary_path = "results/multimodel/summary.csv"
if os.path.exists(summary_path):
    done_df = pd.read_csv(summary_path)
    for _, row in done_df.iterrows():
        key = (row["model"], row["dataset"], int(row["chunk_size"]),
               int(row["top_k"]), row["prompt_strategy"])
        completed.add(key)
    print(f"[Resume] Found {len(completed)} completed configs, skipping them.")
    all_scores = done_df.to_dict("records")
else:
    all_scores = []

# ── Load datasets ─────────────────────────────────────────────────────────────
print("[Setup] Loading datasets...")
squad_docs,  squad_qas  = load_squad(max_papers=N_PAPERS)
pubmed_docs, pubmed_qas = load_pubmedqa(max_papers=N_PAPERS)

dataset_map = {
    "squad":    (squad_docs,  squad_qas),
    "pubmedqa": (pubmed_docs, pubmed_qas),
}

print("[Setup] Loading NLI detector...")
detector = HallucinationDetector()

configs = list(product(MODELS, DATASETS, CHUNKS, TOPKS, PROMPTS))
remaining = [(m,d,c,k,p) for m,d,c,k,p in configs
             if (m,d,c,k,p) not in completed]

print(f"[Setup] Total configs: {len(configs)}")
print(f"[Setup] Already done:  {len(completed)}")
print(f"[Setup] Remaining:     {len(remaining)}")
print(f"[Setup] Questions per config: {N_QUESTIONS}")
print(f"[Setup] Remaining queries: {len(remaining) * N_QUESTIONS}")

for run_i, (model, dataset, chunk_size, top_k, prompt_strategy) in enumerate(remaining):
    print(f"\n{'='*65}")
    print(f"[{run_i+1}/{len(remaining)}] model={model} | dataset={dataset} | chunk={chunk_size} | k={top_k} | prompt={prompt_strategy}")
    print(f"{'='*65}")

    docs, qas = dataset_map[dataset]
    n_q = min(N_QUESTIONS, len(qas))

    pipeline = RAGPipeline(
        chunk_size=chunk_size,
        chunk_overlap=int(chunk_size * 0.1),
        top_k=top_k,
        model_name=model
    )
    collection_name = f"{dataset}_{model}_{chunk_size}_{top_k}".replace("-","_")
    pipeline.index_documents(docs, collection_name=collection_name)

    results = []
    for qa in tqdm(qas[:n_q], desc=f"Querying ({model}, {dataset})"):
        try:
            result = pipeline.query(qa["question"])
            nli = detector.detect(result["answer"], result["context"])
            results.append({
                "model": model,
                "dataset": dataset,
                "chunk_size": chunk_size,
                "top_k": top_k,
                "prompt_strategy": prompt_strategy,
                "question": qa["question"],
                "answer": result["answer"],
                "ground_truth": qa["ground_truth"],
                "faithfulness_score": nli["faithfulness_score"],
                "is_hallucination": nli["is_hallucination"],
                "nli_label": nli["label"],
                "latency_s": result["latency_s"],
            })
        except Exception as e:
            print(f"Warning: {e}")
            continue

    if not results:
        print("Warning: no results, skipping")
        continue

    avg_faith   = sum(r["faithfulness_score"] for r in results) / len(results)
    halluc_rate = sum(1 for r in results if r["is_hallucination"]) / len(results)

    scores = {
        "model": model,
        "dataset": dataset,
        "chunk_size": chunk_size,
        "top_k": top_k,
        "prompt_strategy": prompt_strategy,
        "nli_faithfulness": round(avg_faith, 4),
        "hallucination_rate": round(halluc_rate, 4),
        "n_samples": len(results),
    }
    all_scores.append(scores)

    fname = f"results/multimodel/{model}_{dataset}_chunk{chunk_size}_k{top_k}_{prompt_strategy}.csv"
    pd.DataFrame(results).to_csv(fname, index=False)
    print(f"Done: {scores}")

    summary = pd.DataFrame(all_scores)
    summary.to_csv(summary_path, index=False)
    with open("results/multimodel/summary.json", "w") as f:
        json.dump(all_scores, f, indent=2)

# ── Final summary ─────────────────────────────────────────────────────────────
summary = pd.DataFrame(all_scores).sort_values("nli_faithfulness", ascending=False)
summary.to_csv(summary_path, index=False)

print("\n\n===== COMPLETE =====")
print(summary.to_string(index=False))

print("\n===== MODEL COMPARISON =====")
for ds in DATASETS:
    print(f"\n{ds.upper()}:")
    for model in MODELS:
        subset = summary[(summary.model==model) & (summary.dataset==ds)]
        if len(subset) > 0:
            print(f"  {model}: avg_faith={subset['nli_faithfulness'].mean():.4f}, avg_halluc={subset['hallucination_rate'].mean():.4f}")