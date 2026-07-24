"""
src/reranker.py — extended cross-encoder reranker with diagnostics.

Extends the original single-method class to support:
  - Over-fetch + rerank pattern (fetch_k > top_k)
  - Per-query diagnostic logs (CCS before/after, CE scores, latency)
  - Fallback to cosine-similarity ranking when CE model unavailable
  - Summary stats over a list of per-query logs
  - Togglable via `enabled` flag (disabled = cosine ordering unchanged)

Backwards-compatible: original Reranker.rerank() method is preserved.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class Reranker:
    """
    Cross-encoder reranker for post-retrieval passage ordering.

    Original interface preserved:
        reranker.rerank(query, docs, top_k) -> List[Document]

    Extended interface (with diagnostics):
        docs, log = reranker.retrieve_and_rerank(query, rag_pipeline, fetch_k, top_k)
        result    = reranker.query_with_reranking(question, rag_pipeline, ...)

    Parameters
    ----------
    model_name : str
        HuggingFace cross-encoder checkpoint.
    enabled : bool
        When False, over-fetch is skipped and cosine-ranked docs are
        returned unchanged — useful for ablation baseline conditions.
    """

    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        enabled: bool = True,
    ):
        self.model_name = model_name
        self.enabled = enabled
        self._fallback = False
        try:
            print(f"[Reranker] Loading: {model_name}")
            self.model = CrossEncoder(model_name)
            print("[Reranker] Ready")
        except Exception as exc:
            logger.warning(
                "Reranker: could not load cross-encoder (%s); "
                "falling back to cosine ordering.",
                exc,
            )
            self.model = None
            self._fallback = True

    # ------------------------------------------------------------------ #
    # Original interface (unchanged)                                        #
    # ------------------------------------------------------------------ #

    def rerank(
        self, query: str, docs: List[Document], top_k: Optional[int] = None
    ) -> List[Document]:
        """
        Re-score and re-order documents by relevance to query.
        Returns top_k most relevant docs (or all if top_k is None).
        """
        if not docs:
            return docs
        if self._fallback or not self.enabled:
            return docs[:top_k] if top_k else docs

        pairs = [(query, doc.page_content[:512]) for doc in docs]
        scores = self.model.predict(pairs)

        scored_docs = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
        reranked = [doc for _, doc in scored_docs]
        return reranked[:top_k] if top_k else reranked

    # ------------------------------------------------------------------ #
    # Extended interface with diagnostics                                   #
    # ------------------------------------------------------------------ #

    def retrieve_and_rerank(
        self,
        query: str,
        rag_pipeline,
        fetch_k: int = 7,
        top_k: int = 3,
    ) -> Tuple[List[Document], Dict]:
        """
        Over-fetch `fetch_k` candidates, rerank, return top `top_k`.

        Returns
        -------
        final_docs : List[Document]
            Reranked passages ready for generation.
        log : Dict
            Per-query diagnostics including CE scores and latency.
        """
        t0 = time.time()

        # --- over-retrieve -----------------------------------------------
        old_k = rag_pipeline.top_k
        rag_pipeline.top_k = fetch_k
        try:
            raw_docs, raw_scores = rag_pipeline.retrieve_with_scores(query)
        finally:
            rag_pipeline.top_k = old_k

        if not raw_docs:
            return [], self._empty_log()

        for doc, score in zip(raw_docs, raw_scores):
            doc.metadata.setdefault("retrieval_score", float(score))

        # --- cosine baseline (disabled / fallback) -----------------------
        if not self.enabled or self._fallback:
            final_docs = raw_docs[:top_k]
            return final_docs, self._build_log(
                raw_docs, final_docs, ce_scores=[], elapsed=time.time() - t0,
                reranked=False,
            )

        # --- cross-encoder scoring ----------------------------------------
        pairs = [(query, d.page_content[:512]) for d in raw_docs]
        ce_scores_raw = self.model.predict(pairs)
        ce_scores = [float(s) for s in ce_scores_raw]

        for doc, score in zip(raw_docs, ce_scores):
            doc.metadata["ce_score"] = score

        ranked = sorted(
            zip(raw_docs, ce_scores), key=lambda x: x[1], reverse=True
        )
        final_docs = [d for d, _ in ranked[:top_k]]
        top_ce = [s for _, s in ranked[:top_k]]

        return final_docs, self._build_log(
            raw_docs, final_docs, ce_scores=top_ce, elapsed=time.time() - t0,
            reranked=True,
        )

    def query_with_reranking(
        self,
        question: str,
        rag_pipeline,
        fetch_k: int = 7,
        top_k: int = 3,
    ) -> Dict:
        """Full end-to-end: retrieve → rerank → generate."""
        docs, rerank_log = self.retrieve_and_rerank(
            question, rag_pipeline, fetch_k=fetch_k, top_k=top_k
        )
        result = rag_pipeline.generate(question, docs)
        result["rerank_log"] = rerank_log
        return result

    # ------------------------------------------------------------------ #
    # Helpers                                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _empty_log() -> Dict:
        return {
            "reranked": False, "fetch_k": 0, "top_k": 0,
            "n_docs_fetched": 0, "n_docs_returned": 0,
            "mean_ce_score": -1.0, "min_ce_score": -1.0,
            "max_ce_score": -1.0, "latency_s": 0.0,
        }

    @staticmethod
    def _build_log(
        raw_docs: List[Document],
        final_docs: List[Document],
        ce_scores: List[float],
        elapsed: float,
        reranked: bool,
    ) -> Dict:
        cs = ce_scores if ce_scores else []
        return {
            "reranked": reranked,
            "fetch_k": len(raw_docs),
            "top_k": len(final_docs),
            "n_docs_fetched": len(raw_docs),
            "n_docs_returned": len(final_docs),
            "mean_ce_score": round(float(np.mean(cs)), 4) if cs else -1.0,
            "min_ce_score": round(float(np.min(cs)), 4) if cs else -1.0,
            "max_ce_score": round(float(np.max(cs)), 4) if cs else -1.0,
            "latency_s": round(elapsed, 3),
        }

    @staticmethod
    def summary_stats(logs: List[Dict]) -> Dict:
        """Aggregate a list of per-query reranker log dicts."""
        if not logs:
            return {}
        n = len(logs)
        valid_ce = [l["mean_ce_score"] for l in logs if l.get("mean_ce_score", -1) >= 0]
        return {
            "n_queries": n,
            "pct_reranked": round(100.0 * sum(1 for l in logs if l.get("reranked")) / n, 1),
            "mean_fetch_k": round(float(np.mean([l.get("fetch_k", 0) for l in logs])), 1),
            "mean_ce_score": round(float(np.mean(valid_ce)), 4) if valid_ce else -1.0,
            "mean_latency_s": round(float(np.mean([l.get("latency_s", 0) for l in logs])), 3),
        }
