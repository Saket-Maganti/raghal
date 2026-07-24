"""
RAGAS-style faithfulness scorer.

This intentionally mirrors the RAGAS faithfulness rubric: judge whether each
answer claim is supported by the retrieved context and return a scalar in
[0, 1].  It uses the configured LLM backend because the full `ragas` package
has several provider-specific dependencies that are not already required by
this repo.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict


JUDGE_PROMPT = """You are evaluating faithfulness in retrieval-augmented QA.

Return JSON only with keys:
  faithfulness_score: a number from 0 to 1
  judge_reason: one short sentence

Score 1.0 if every factual claim in the answer is directly supported by the
context. Score 0.0 if the answer is unsupported or contradicted. Use partial
credit when some but not all claims are supported.

Question:
{question}

Context:
{context}

Answer:
{answer}

JSON:"""


class RagasScorer:
    def __init__(
        self,
        judge_backend: str = "ollama",
        judge_model: str = "mistral",
        temperature: float = 0.0,
    ):
        self.judge_backend = judge_backend
        self.judge_model = judge_model
        self.temperature = temperature
        self.llm = self._make_llm()

    def _make_llm(self):
        if self.judge_backend == "groq":
            from src.groq_llm import GroqLLM

            return GroqLLM(model=self.judge_model, temperature=self.temperature)
        if self.judge_backend == "together":
            from src.together_llm import TogetherLLM

            return TogetherLLM(model=self.judge_model, temperature=self.temperature)
        from langchain_ollama import OllamaLLM

        base_url = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST")
        if base_url and not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"
        if base_url:
            return OllamaLLM(
                model=self.judge_model,
                temperature=self.temperature,
                base_url=base_url,
            )
        return OllamaLLM(model=self.judge_model, temperature=self.temperature)

    def score(self, answer: str, context: str, question: str = "") -> Dict[str, Any]:
        prompt = JUDGE_PROMPT.format(
            question=question[:1000],
            context=context[:4000],
            answer=answer[:1500],
        )
        raw = self.llm.invoke(prompt)
        score, reason = self._parse(raw)
        return {
            "faithfulness_score": score,
            "judge_reason": reason,
            "raw": raw[:1000],
        }

    @staticmethod
    def _parse(raw: str) -> tuple[float, str]:
        text = (raw or "").strip()
        try:
            blob = json.loads(text)
            score = float(blob.get("faithfulness_score", 0.0))
            reason = str(blob.get("judge_reason", ""))
            return max(0.0, min(1.0, score)), reason
        except Exception:
            pass
        match = re.search(r"([01](?:\.\d+)?)", text)
        score = float(match.group(1)) if match else 0.0
        return max(0.0, min(1.0, score)), text[:200]
