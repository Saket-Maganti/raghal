import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import os, json, time
import pandas as pd
from tqdm import tqdm
from src.data_loader import load_qasper as load_squad
from src.pubmedqa_loader import load_pubmedqa
from src.hallucination_detector import HallucinationDetector
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

os.makedirs("results/zeroshot", exist_ok=True)

MODELS = ["mistral", "llama3"]
N_PAPERS = 50
N_QUESTIONS = 100

PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are a helpful assistant. Answer the following question as accurately as possible based on your knowledge.

Question: {question}

Answer:"""
)

print("[Setup] Loading datasets...")
squad_docs, squad_qas = load_squad(max_papers=N_PAPERS)
pubmed_docs, pubmed_qas = load_pubmedqa(max_papers=N_PAPERS)

print("[Setup] Loading NLI detector...")
detector = HallucinationDetector()

all_scores = []

for model in MODELS:
    print(f"\n[ZeroShot] Loading model: {model}")
    llm = OllamaLLM(model=model, temperature=0.1)

    for dataset, qas in [("squad", squad_qas), ("pubmedqa", pubmed_qas)]:
        n_q = min(N_QUESTIONS, len(qas))
        print(f"\n{'='*60}")
        print(f"model={model} | dataset={dataset} | n={n_q}")
        print(f"{'='*60}")

        results = []
        for qa in tqdm(qas[:n_q], desc=f"Zero-shot ({model},{dataset})"):
            try:
                t0 = time.time()
                answer = llm.invoke(PROMPT.format(question=qa["question"]))
                latency = round(time.time() - t0, 2)
                nli = detector.detect(answer, qa["ground_truth"])
                results.append({
                    "model": model,
                    "dataset": dataset,
                    "question": qa["question"],
                    "answer": answer,
                    "ground_truth": qa["ground_truth"],
                    "faithfulness_score": nli["faithfulness_score"],
                    "is_hallucination": nli["is_hallucination"],
                    "latency_s": latency,
                })
            except Exception as e:
                print(f"Warning: {e}")
                continue

        if not results:
            continue

        avg_faith = sum(r["faithfulness_score"] for r in results) / len(results)
        halluc_rate = sum(1 for r in results if r["is_hallucination"]) / len(results)

        scores = {
            "model": model,
            "dataset": dataset,
            "nli_faithfulness": round(avg_faith, 4),
            "hallucination_rate": round(halluc_rate, 4),
            "n_samples": len(results),
        }
        all_scores.append(scores)
        pd.DataFrame(results).to_csv(f"results/zeroshot/{model}_{dataset}.csv", index=False)
        pd.DataFrame(all_scores).to_csv("results/zeroshot/summary.csv", index=False)
        print(f"Done: {scores}")

print("\n===== ZERO-SHOT COMPLETE =====")
summary = pd.DataFrame(all_scores)
print(summary.to_string(index=False))

rag_best = {
    ("mistral", "squad"):    (0.7775, 0.03),
    ("mistral", "pubmedqa"): (0.6004, 0.20),
    ("llama3",  "squad"):    (0.7752, 0.00),
    ("llama3",  "pubmedqa"): (0.6233, 0.10),
}

print("\n===== RAG BENEFIT vs ZERO-SHOT =====")
for s in all_scores:
    key = (s["model"], s["dataset"])
    if key in rag_best:
        rf, rh = rag_best[key]
        print(f"\n{s['model']}/{s['dataset']}:")
        print(f"  Zero-shot: faith={s['nli_faithfulness']:.4f}, halluc={s['hallucination_rate']*100:.1f}%")
        print(f"  Best RAG:  faith={rf:.4f}, halluc={rh*100:.1f}%")
        print(f"  RAG benefit: faith +{rf-s['nli_faithfulness']:.4f}, halluc -{(s['hallucination_rate']-rh)*100:.1f}pp")