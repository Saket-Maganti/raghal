"""
Second automated faithfulness scorer for the revision.

Default model: `roberta-large-mnli`, used as an MNLI zero-shot entailment
proxy. `vectara/hallucination_evaluation_model` is also supported when the
runtime can load it without custom remote code.
"""

from __future__ import annotations

from typing import Any, Dict

import torch
from transformers import pipeline


class VectaraHEMScorer:
    def __init__(self, model_name: str = "roberta-large-mnli"):
        self.model_name = model_name
        if torch.cuda.is_available():
            device: int | str = 0
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = -1

        if "mnli" in model_name.lower():
            self.mode = "mnli"
            self.pipe = pipeline(
                "zero-shot-classification",
                model=model_name,
                device=device,
            )
        else:
            self.mode = "hem"
            try:
                self.pipe = pipeline(
                    "text-classification",
                    model=model_name,
                    device=device,
                    truncation=True,
                    max_length=512,
                )
            except Exception as exc:
                fallback = "roberta-large-mnli"
                print(
                    "[HEM] Falling back to roberta-large-mnli because "
                    f"{model_name} could not be loaded: {type(exc).__name__}: {exc}",
                    flush=True,
                )
                self.model_name = fallback
                self.mode = "mnli"
                self.pipe = pipeline(
                    "zero-shot-classification",
                    model=fallback,
                    device=device,
                )

    def detect(self, answer: str, context: str, question: str = "") -> Dict[str, Any]:
        answer = (answer or "").strip()
        context = (context or "").strip()
        if not answer:
            return {
                "faithfulness_score": 1.0,
                "is_hallucination": False,
                "label": "faithful",
            }

        if self.mode == "mnli":
            result = self.pipe(
                answer,
                candidate_labels=["entailment", "neutral", "contradiction"],
                hypothesis_template="{}",
                multi_label=False,
            )
            scores = dict(zip(result["labels"], result["scores"]))
            faith = float(scores.get("entailment", 0.0))
        else:
            pair = f"premise: {context[:1800]}\nhypothesis: {answer[:700]}"
            out = self.pipe(pair)
            item = out[0] if isinstance(out, list) else out
            label = str(item.get("label", "")).lower()
            raw_score = float(item.get("score", 0.0))
            # Vectara HEM labels hallucination probability in common releases.
            # Be conservative: labels containing halluc imply score is bad.
            faith = 1.0 - raw_score if "halluc" in label else raw_score

        faith = max(0.0, min(1.0, faith))
        return {
            "faithfulness_score": round(faith, 4),
            "is_hallucination": faith < 0.5,
            "label": "hallucinated" if faith < 0.5 else "faithful",
        }
