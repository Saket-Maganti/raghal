import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import os
import json
import pandas as pd
from itertools import product
from tqdm import tqdm
from src.pubmedqa_loader import load_pubmedqa
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector

ABLATION_CONFIG = {
    "chunk_sizes": [256, 512, 1024],
    "top_ks": [3, 5],
    "prompt_strategies": ["strict", "cot"],
}

os.makedirs("results/pubmedqa", exist_ok=True)
print("[PubMedQA] Loading dataset...")
documents, qa_pairs = load_pubmedqa(max_papers=30)
print("[PubMedQA] Loading hallucination detector...")
detector = HallucinationDetector()
configs = list(product(ABLATION_CONFIG["chunk_sizes"], ABLATION_CONFIG["top_ks"], ABLATION_CONFIG["prompt_strategies"]))
all_scores = []

for i, (chunk_size, top_k, prompt_strategy) in enumerate(configs):
    print(f"\n[{i+1}/12] chunk={chunk_size} | k={top_k} | prompt={prompt_strategy}")
    pipeline = RAGPipeline(chunk_size=chunk_size, chunk_overlap=int(chunk_size*0.1), top_k=top_k)
    pipeline.index_documents(documents, collection_name=f"pubmed_{i}_{chunk_size}_{top_k}")
    results = []
    for qa in tqdm(qa_pairs[:30], desc="Querying"):
        try:
            result = pipeline.query(qa["question"])
            nli = detector.detect(result["answer"], result["context"])
            results.append({**result, "ground_truth": qa["ground_truth"], "faithfulness_score": nli["faithfulness_score"], "is_hallucination": nli["is_hallucination"], "chunk_size": chunk_size, "top_k": top_k, "prompt_strategy": prompt_strategy})
        except Exception as e:
            print(f"Warning: {e}")
    avg_faith = sum(r["faithfulness_score"] for r in results) / len(results)
    halluc_rate = sum(1 for r in results if r["is_hallucination"]) / len(results)
    scores = {"dataset": "pubmedqa", "chunk_size": chunk_size, "top_k": top_k, "prompt_strategy": prompt_strategy, "nli_faithfulness": round(avg_faith, 4), "hallucination_rate": round(halluc_rate, 4), "n_samples": len(results)}
    all_scores.append(scores)
    pd.DataFrame(results).to_csv(f"results/pubmedqa/ablation_chunk{chunk_size}_k{top_k}_{prompt_strategy}.csv", index=False)
    print(f"Done: {scores}")

summary = pd.DataFrame(all_scores).sort_values("nli_faithfulness", ascending=False)
summary.to_csv("results/pubmedqa/ablation_summary.csv", index=False)
with open("results/pubmedqa/ablation_summary.json", "w") as f:
    json.dump(all_scores, f, indent=2)
print("\n===== PUBMEDQA ABLATION SUMMARY =====")
print(summary.to_string(index=False))
