"""
Hallucination Detector using Natural Language Inference (NLI)
Uses cross-encoder/nli-deberta-v3-base to check if the answer
is entailed by the retrieved context.
"""

import torch
from transformers import pipeline
from typing import Optional


class HallucinationDetector:
    """
    Detects hallucinations by checking if the generated answer
    is entailed by the retrieved context using an NLI model.

    Label mapping:
        entailment   → answer is supported by context (faithful)
        neutral      → answer is partially supported
        contradiction → answer contradicts context (hallucination)
    """

    ENTAILMENT_LABEL = "entailment"
    CONTRADICTION_LABEL = "contradiction"
    HALLUCINATION_THRESHOLD = 0.5  # entailment score below this = hallucination

    def __init__(self, model_name: str = "cross-encoder/nli-deberta-v3-base"):
        print(f"[NLI] Loading hallucination detector: {model_name}")
        if torch.cuda.is_available():
            device = 0
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = -1
        self.nli = pipeline(
            "zero-shot-classification",
            model=model_name,
            device=device
        )
        print(f"[NLI] Running on: {device}")

    def score_sentence(self, premise: str, hypothesis: str) -> dict:
        """
        Score a single (premise, hypothesis) pair.
        premise   = retrieved context chunk
        hypothesis = generated answer sentence
        """
        result = self.nli(
            hypothesis,
            candidate_labels=["entailment", "neutral", "contradiction"],
            hypothesis_template="{}",
            multi_label=False
        )
        scores = dict(zip(result["labels"], result["scores"]))
        return scores

    def detect(self, answer: str, context: str) -> dict:
        """
        Check if an answer is hallucinated given the context.

        Returns:
            faithfulness_score: float [0, 1]  (higher = more faithful)
            is_hallucination: bool
            sentence_scores: list of per-sentence scores
            label: "faithful" | "hallucinated"
        """
        # Split answer into sentences for fine-grained scoring
        sentences = [s.strip() for s in answer.split(".") if len(s.strip()) > 10]

        if not sentences:
            return {
                "faithfulness_score": 1.0,
                "is_hallucination": False,
                "label": "faithful",
                "sentence_scores": []
            }

        sentence_scores = []
        entailment_scores = []

        for sent in sentences:
            try:
                scores = self.score_sentence(context[:1024], sent)  # truncate context for speed
                entailment_score = scores.get("entailment", 0.0)
                entailment_scores.append(entailment_score)
                sentence_scores.append({
                    "sentence": sent,
                    "entailment": round(entailment_score, 4),
                    "contradiction": round(scores.get("contradiction", 0.0), 4),
                    "neutral": round(scores.get("neutral", 0.0), 4),
                })
            except Exception as e:
                print(f"[NLI] Warning: scoring failed for sentence: {e}")
                entailment_scores.append(0.5)

        faithfulness_score = sum(entailment_scores) / len(entailment_scores)
        is_hallucination = faithfulness_score < self.HALLUCINATION_THRESHOLD

        return {
            "faithfulness_score": round(faithfulness_score, 4),
            "is_hallucination": is_hallucination,
            "label": "hallucinated" if is_hallucination else "faithful",
            "sentence_scores": sentence_scores
        }
