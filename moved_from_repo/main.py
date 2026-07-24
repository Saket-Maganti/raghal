"""
Main entry point for RAG Hallucination Detection project.
Run modes:
    python main.py --mode demo       # quick single query demo
    python main.py --mode eval       # full evaluation
    python main.py --mode ablation   # full ablation study
"""

import argparse
import os
import pandas as pd
from tqdm import tqdm

from src.data_loader import load_qasper
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.ablation import run_full_ablation


def demo_mode():
    """Quick demo: index a few papers and run a query."""
    print("\n=== DEMO MODE ===\n")
    documents, qa_pairs = load_qasper(max_papers=5)

    pipeline = RAGPipeline(chunk_size=512, top_k=3)
    pipeline.index_documents(documents)

    detector = HallucinationDetector()

    qa = qa_pairs[0]
    print(f"\nQuestion: {qa['question']}")
    print(f"Ground Truth: {qa['ground_truth']}\n")

    result = pipeline.query(qa["question"])
    nli = detector.detect(result["answer"], result["context"])

    print(f"Generated Answer:\n{result['answer']}\n")
    print(f"Faithfulness Score: {nli['faithfulness_score']}")
    print(f"Hallucination: {nli['is_hallucination']} ({nli['label']})")
    print(f"Latency: {result['latency_s']}s")


def eval_mode(n_papers: int = 30, n_questions: int = 50):
    """Full evaluation using NLI scores."""
    print("\n=== EVALUATION MODE ===\n")
    documents, qa_pairs = load_qasper(max_papers=n_papers)

    pipeline = RAGPipeline(chunk_size=512, top_k=3)
    pipeline.index_documents(documents)

    detector = HallucinationDetector()

    results = []
    for qa in tqdm(qa_pairs[:n_questions], desc="Evaluating"):
        try:
            result = pipeline.query(qa["question"])
            nli = detector.detect(result["answer"], result["context"])
            results.append({
                "question": result["question"],
                "answer": result["answer"],
                "ground_truth": qa["ground_truth"],
                "faithfulness_score": nli["faithfulness_score"],
                "is_hallucination": nli["is_hallucination"],
                "label": nli["label"],
                "latency_s": result["latency_s"],
            })
        except Exception as e:
            print(f"Warning: {e}")

    os.makedirs("results", exist_ok=True)
    avg_faith = sum(r["faithfulness_score"] for r in results) / len(results)
    halluc_rate = sum(1 for r in results if r["is_hallucination"]) / len(results)

    print(f"\n=== RESULTS ===")
    print(f"Faithfulness Score:  {avg_faith:.4f}")
    print(f"Hallucination Rate:  {halluc_rate:.4f}")
    print(f"Samples evaluated:   {len(results)}")

    pd.DataFrame(results).to_csv("results/eval_results.csv", index=False)
    print("Saved to results/eval_results.csv")


def ablation_mode():
    """Full ablation study."""
    print("\n=== ABLATION MODE ===\n")
    run_full_ablation(n_papers=30, n_questions=30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Hallucination Detection")
    parser.add_argument(
        "--mode",
        choices=["demo", "eval", "ablation"],
        default="demo",
        help="Run mode"
    )
    parser.add_argument("--n_papers", type=int, default=30)
    parser.add_argument("--n_questions", type=int, default=50)
    args = parser.parse_args()

    if args.mode == "demo":
        demo_mode()
    elif args.mode == "eval":
        eval_mode(args.n_papers, args.n_questions)
    elif args.mode == "ablation":
        ablation_mode()