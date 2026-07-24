"""
Evaluation using RAGAS metrics + custom hallucination rate
"""

import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_ollama import OllamaLLM
from langchain_community.embeddings import HuggingFaceEmbeddings


def evaluate_rag(results: list[dict]) -> dict:
    """
    Run RAGAS evaluation on RAG results.

    Args:
        results: list of {question, answer, context, is_hallucination}

    Returns:
        dict with faithfulness, answer_relevancy, hallucination_rate
    """
    print("[Eval] Running RAGAS evaluation...")

    # Build HuggingFace Dataset for RAGAS
    data = {
        "question": [r["question"] for r in results],
        "answer": [r["answer"] for r in results],
        "contexts": [[r["context"]] for r in results],
        "ground_truth": [r.get("ground_truth", "") for r in results],
    }
    ds = Dataset.from_dict(data)

    # Wire up local LLM + embeddings for RAGAS
    llm = LangchainLLMWrapper(OllamaLLM(model="mistral", temperature=0.0))
    emb = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": __import__("torch").cuda.is_available() and "cuda" or "cpu"}
        )
    )

    result = evaluate(
        ds,
        metrics=[faithfulness, answer_relevancy],
        llm=llm,
        embeddings=emb,
        raise_exceptions=False,
    )

    # Hallucination rate from NLI detector
    hallucination_count = sum(1 for r in results if r.get("is_hallucination", False))
    hallucination_rate = hallucination_count / len(results) if results else 0.0

    scores = {
        "faithfulness": round(float(result["faithfulness"]), 4),
        "answer_relevancy": round(float(result["answer_relevancy"]), 4),
        "hallucination_rate": round(hallucination_rate, 4),
        "n_samples": len(results),
        "n_hallucinated": hallucination_count,
    }

    print(f"[Eval] Results:")
    print(f"       Faithfulness:       {scores['faithfulness']:.4f}  (target > 0.85)")
    print(f"       Answer Relevancy:   {scores['answer_relevancy']:.4f}  (target > 0.80)")
    print(f"       Hallucination Rate: {scores['hallucination_rate']:.4f}  (target < 0.12)")

    return scores


def save_results(results: list[dict], scores: dict, path: str = "results/results.csv"):
    """Save per-sample results and aggregate scores to CSV."""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)

    rows = []
    for r in results:
        rows.append({
            "question": r["question"],
            "answer": r["answer"][:300],
            "faithfulness_score": r.get("faithfulness_score", ""),
            "is_hallucination": r.get("is_hallucination", ""),
            "latency_s": r.get("latency_s", ""),
            "chunk_size": r.get("chunk_size", ""),
            "top_k": r.get("top_k", ""),
            "prompt_strategy": r.get("prompt_strategy", ""),
        })

    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)

    scores_path = path.replace(".csv", "_scores.csv")
    pd.DataFrame([scores]).to_csv(scores_path, index=False)

    print(f"[Eval] Saved results to {path}")
    print(f"[Eval] Saved scores to {scores_path}")
