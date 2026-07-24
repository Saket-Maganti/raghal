"""
src/crag_retriever.py
CRAG (Corrective Retrieval-Augmented Generation; Yan et al. 2024) — a
faithful reimplementation against the published algorithm because no
official end-to-end checkpoint is released.

CRAG's pipeline (per query):

    1. Retrieve top-k passages from the static corpus.
    2. Run a *retrieval evaluator* on each passage that emits one of three
       confidence labels:
         CORRECT    — passage strongly supports the query
         AMBIGUOUS  — partial / uncertain support
         INCORRECT  — the passage is irrelevant or contradicts the query
    3. Aggregate per-passage labels into a query-level decision:
         CORRECT     → "internal knowledge" path: use refined passages
         AMBIGUOUS   → "hybrid" path: refine internal passages + augment with
                       web-search results
         INCORRECT   → "external knowledge" path: discard internal passages,
                       use web search exclusively (with knowledge refinement)
    4. *Knowledge refinement*: decompose each retained passage into "strips"
       (sentences / sub-paragraphs), score each strip, and keep the most
       relevant strips. The strips are then re-ordered and concatenated for
       the generator.

The published evaluator is a fine-tuned T5-large with private training data.
Following standard reimplementation practice we substitute a cross-encoder
(`cross-encoder/ms-marco-MiniLM-L-6-v2`) and threshold its raw logits to
recover the same 3-bucket confidence signal:

    logit > +1.0  → CORRECT
    logit < -1.0  → INCORRECT
    otherwise     → AMBIGUOUS

Web search is mocked behind an injectable callable so the head-to-head
comparison can either:
    (a) use a live search API (unbounded scope), or
    (b) substitute a local DuckDuckGo client, or
    (c) supply a static "no web access" fallback that returns []
We default to (c) so all comparisons run in a closed environment unless
explicitly opted-in.

This wrapper exposes the same `retrieve(query) -> (docs, log)` shape as the
HCPC retrievers so it can be slotted into the head-to-head harness directly.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

import numpy as np
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


# ── Default thresholds ───────────────────────────────────────────────────────
DEFAULT_CORRECT_THRESHOLD   = 1.0    # CE logit ABOVE → CORRECT
DEFAULT_INCORRECT_THRESHOLD = -1.0   # CE logit BELOW → INCORRECT
DEFAULT_STRIP_TOP_K         = 3      # how many strips to keep per passage


WebSearchFn = Callable[[str, int], List[Document]]


def _no_web_search(query: str, k: int = 3) -> List[Document]:
    return []


@dataclass
class CRAGLog:
    per_passage_labels: List[str]
    query_decision:     str           # "correct" | "ambiguous" | "incorrect"
    n_strips_kept:      int
    web_results_used:   int
    final_n_passages:   int
    eval_logits:        List[float]


class CRAGRetriever:
    """
    Reimplementation of CRAG, following the algorithm description in
    Yan et al. 2024 §3. The cross-encoder substitution is documented in
    the module docstring and reported transparently in the paper.
    """

    STRATEGY = "crag"

    def __init__(
        self,
        pipeline: Any,
        web_search: Optional[WebSearchFn] = None,
        ce_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        correct_threshold:   float = DEFAULT_CORRECT_THRESHOLD,
        incorrect_threshold: float = DEFAULT_INCORRECT_THRESHOLD,
        strip_top_k:         int   = DEFAULT_STRIP_TOP_K,
    ):
        self.pipeline           = pipeline
        self.web_search         = web_search or _no_web_search
        self.correct_threshold   = correct_threshold
        self.incorrect_threshold = incorrect_threshold
        self.strip_top_k         = strip_top_k
        self.top_k               = pipeline.top_k
        print(f"[CRAG] Loading evaluator (cross-encoder proxy): {ce_model_name}")
        self._ce = CrossEncoder(ce_model_name)
        print(f"[CRAG] Ready. correct>{correct_threshold}, "
              f"incorrect<{incorrect_threshold}, web={'enabled' if web_search else 'disabled'}")

    # ── Public API ───────────────────────────────────────────────────────────

    def retrieve(self, query: str) -> Tuple[List[Document], dict]:
        raw_docs, _sims = self.pipeline.retrieve_with_scores(query)
        if not raw_docs:
            return [], _empty_log()

        # 1. Evaluator on each passage
        pairs = [(query, d.page_content[:512]) for d in raw_docs]
        try:
            logits = [float(s) for s in self._ce.predict(pairs)]
        except Exception as exc:
            logger.warning("[CRAG] CE eval failed: %s", exc)
            logits = [0.0] * len(raw_docs)

        labels = [self._label_for(l) for l in logits]

        # 2. Aggregate decision
        if any(lab == "correct" for lab in labels):
            decision = "correct"
        elif all(lab == "incorrect" for lab in labels):
            decision = "incorrect"
        else:
            decision = "ambiguous"

        # 3. Branch-specific assembly
        web_docs: List[Document] = []
        if decision in ("ambiguous", "incorrect"):
            web_docs = list(self.web_search(query, k=self.top_k))

        if decision == "incorrect":
            kept = web_docs
        elif decision == "ambiguous":
            kept = [d for d, l in zip(raw_docs, labels) if l != "incorrect"] + web_docs
        else:
            kept = [d for d, l in zip(raw_docs, labels) if l != "incorrect"]

        # 4. Knowledge refinement: decompose each kept passage into strips
        #    and keep the top-scoring strips.
        refined: List[Document] = []
        n_strips_kept = 0
        for doc in kept:
            strips = self._decompose_to_strips(doc.page_content)
            if not strips:
                continue
            strip_scores = self._safe_ce([(query, s) for s in strips])
            order = np.argsort(strip_scores)[::-1]
            top = order[: self.strip_top_k]
            top_text = " ".join(strips[i] for i in sorted(top))
            n_strips_kept += len(top)
            new_meta = dict(doc.metadata)
            new_meta["crag_strip_count"] = int(len(top))
            refined.append(Document(page_content=top_text, metadata=new_meta))

        if not refined and raw_docs:
            # safety: never starve the generator
            refined = raw_docs[: self.top_k]

        final = refined[: self.top_k]

        log = {
            "strategy":          self.STRATEGY,
            "per_passage_labels": labels,
            "query_decision":    decision,
            "n_strips_kept":     n_strips_kept,
            "web_results_used":  len(web_docs),
            "final_n_passages":  len(final),
            "eval_logits":       [round(l, 4) for l in logits],
            "refined":           True,           # CRAG always operates on the set
            "context_coherence": -1.0,           # not natively computed
        }
        return final, log

    # ── Internals ────────────────────────────────────────────────────────────

    def _label_for(self, logit: float) -> str:
        if logit > self.correct_threshold:
            return "correct"
        if logit < self.incorrect_threshold:
            return "incorrect"
        return "ambiguous"

    def _decompose_to_strips(self, text: str) -> List[str]:
        """
        Sentence-level decomposition. CRAG calls these "knowledge strips".
        Filter out very short fragments to avoid trivial strips.
        """
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        return [p for p in parts if len(p) > 30]

    def _safe_ce(self, pairs: List[Tuple[str, str]]) -> np.ndarray:
        if not pairs:
            return np.array([])
        try:
            return np.asarray(self._ce.predict(pairs), dtype=float)
        except Exception:
            return np.zeros(len(pairs), dtype=float)


def _empty_log() -> dict:
    return {
        "strategy":           "crag",
        "per_passage_labels": [],
        "query_decision":     "incorrect",
        "n_strips_kept":      0,
        "web_results_used":   0,
        "final_n_passages":   0,
        "eval_logits":        [],
        "refined":            False,
        "context_coherence":  -1.0,
    }
