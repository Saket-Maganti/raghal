"""
Re-ranker Ablation Study.

Compares RAG with and without re-ranking across:
- 2 datasets (SQuAD, PubMedQA)
- 2 models (Mistral, Llama-3)
- 3 chunk sizes (256, 512, 1024)
- top_k=5 retrieve, top_k=3 after reranking (fixed)
- prompt=strict (fixed — best performer)

Research question:
"Does re-ranking reduce the chunk-size dependency found in the ablation study?"

Results saved to results/reranker/
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import os
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
import json
import pandas as pd
from tqdm import tqdm

from src.data_loader import load_qasper as load_squad
from src.pubmedqa_loader import load_pubmedqa
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.reranker import Reranker

MODELS   = ["mistral", "llama3"]
DATASETS = ["squad", "pubmedqa"]
CHUNKS   = [256, 512, 1024]
N_PAPERS = 50
N_QUESTIONS = 100
RETRIEVE_K = 5    # retrieve more, then rerank down to 3
RERANK_K   = 3

os.makedirs("results/reranker", exist_ok=True)

completed = set()
summary_path = "results/reranker/summary.csv"
all_scores = []
if os.path.exists(summary_path):
    done_df = pd.read_csv(summary_path)
    for _, row in done_df.iterrows():
        completed.add((row["model"], row["dataset"], int(row["chunk_size"]), row["condition"]))
    all_scores = done_df.to_dict("records")
    print(f"[Resume] Skipping {len(completed)} completed configs")

print("[Setup] Loading datasets...")
squad_docs,  squad_qas  = load_squad(max_papers=N_PAPERS)
pubmed_docs, pubmed_qas = load_pubmedqa(max_papers=N_PAPERS)
dataset_map = {
    "squad":    (squad_docs,  squad_qas),
    "pubmedqa": (pubmed_docs, pubmed_qas),
}

print("[Setup] Loading NLI detector...")
detector = HallucinationDetector()

print("[Setup] Loading re-ranker...")
reranker = Reranker()

configs = [(m, d, c) for m in MODELS for d in DATASETS for c in CHUNKS]
print(f"[Setup] {len(configs)} configs × 2 conditions (with/without reranker) × {N_QUESTIONS} questions")
print(f"[Setup] Total queries: {len(configs) * 2 * N_QUESTIONS}")

all_scores = []

for run_i, (model, dataset, chunk_size) in enumerate(configs):
    docs, qas = dataset_map[dataset]
    n_q = min(N_QUESTIONS, len(qas))

    for use_reranker in [False, True]:
        condition = "reranked" if use_reranker else "baseline"
        if (model, dataset, chunk_size, condition) in completed:
            print(f"Skipping {model}/{dataset}/chunk{chunk_size}/{condition}")
            continue
        top_k = RETRIEVE_K if use_reranker else RERANK_K

        print(f"\n{'='*65}")
        print(f"[{run_i*2 + (1 if use_reranker else 0) + 1}/{len(configs)*2}] "
              f"model={model} | dataset={dataset} | chunk={chunk_size} | {condition}")
        print(f"{'='*65}")

        pipeline = RAGPipeline(
            chunk_size=chunk_size,
            chunk_overlap=int(chunk_size * 0.1),
            top_k=top_k,
            model_name=model
        )
        collection_name = f"rr_{dataset}_{model}_{chunk_size}".replace("-", "_")
        pipeline.index_documents(docs, collection_name=collection_name)

        results = []
        for qa in tqdm(qas[:n_q], desc=f"{condition} ({model}, {dataset})"):
            try:
                # Retrieve
                retrieved = pipeline.retrieve(qa["question"])

                # Re-rank if enabled
                if use_reranker:
                    retrieved = reranker.rerank(qa["question"], retrieved, top_k=RERANK_K)

                # Generate
                result = pipeline.generate(qa["question"], retrieved)
                nli = detector.detect(result["answer"], result["context"])

                results.append({
                    "model": model,
                    "dataset": dataset,
                    "chunk_size": chunk_size,
                    "condition": condition,
                    "question": qa["question"],
                    "answer": result["answer"],
                    "ground_truth": qa["ground_truth"],
                    "faithfulness_score": nli["faithfulness_score"],
                    "is_hallucination": nli["is_hallucination"],
                    "latency_s": result["latency_s"],
                })
            except Exception as e:
                print(f"Warning: {e}")
                continue

        if not results:
            continue

        avg_faith   = sum(r["faithfulness_score"] for r in results) / len(results)
        halluc_rate = sum(1 for r in results if r["is_hallucination"]) / len(results)

        scores = {
            "model": model,
            "dataset": dataset,
            "chunk_size": chunk_size,
            "condition": condition,
            "nli_faithfulness": round(avg_faith, 4),
            "hallucination_rate": round(halluc_rate, 4),
            "n_samples": len(results),
        }
        all_scores.append(scores)

        fname = f"results/reranker/{model}_{dataset}_chunk{chunk_size}_{condition}.csv"
        pd.DataFrame(results).to_csv(fname, index=False)
        print(f"Done: {scores}")

        pd.DataFrame(all_scores).to_csv("results/reranker/summary.csv", index=False)
        with open("results/reranker/summary.json", "w") as f:
            json.dump(all_scores, f, indent=2)

# ── Final analysis ────────────────────────────────────────────────────────────
summary = pd.DataFrame(all_scores)
summary.to_csv("results/reranker/summary.csv", index=False)

print("\n\n===== RERANKER ABLATION COMPLETE =====")
print(summary.sort_values(["model","dataset","chunk_size"]).to_string(index=False))

print("\n===== RERANKER IMPACT =====")
for ds in DATASETS:
    print(f"\n{ds.upper()}:")
    for model in MODELS:
        print(f"  {model}:")
        for chunk in CHUNKS:
            base = summary[(summary.model==model)&(summary.dataset==ds)&
                          (summary.chunk_size==chunk)&(summary.condition=="baseline")]
            rr   = summary[(summary.model==model)&(summary.dataset==ds)&
                          (summary.chunk_size==chunk)&(summary.condition=="reranked")]
            if len(base) and len(rr):
                faith_diff = rr.iloc[0]["nli_faithfulness"] - base.iloc[0]["nli_faithfulness"]
                halluc_diff = rr.iloc[0]["hallucination_rate"] - base.iloc[0]["hallucination_rate"]
                print(f"    chunk={chunk}: faith {faith_diff:+.4f} | halluc {halluc_diff*100:+.1f}pp")