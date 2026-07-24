"""
integrations/langchain/coherence_gated_retriever.py — Phase 5 #12
=================================================================

A drop-in LangChain `BaseRetriever` that wraps any underlying retriever
with a CCS-based decision policy. Designed as the contrib PR draft for
upstream langchain (see `INTEGRATION_NOTES.md` next to this file).

Usage::

    from langchain_community.vectorstores import Chroma
    from langchain.retrievers import CoherenceGatedRetriever
    # (after upstream merge — for now: import from this file directly)

    base = vectorstore.as_retriever(search_kwargs={"k": 5})
    gated = CoherenceGatedRetriever(
        base_retriever=base,
        embeddings=embeddings,
        ccs_threshold=0.5,
        on_low_coherence="expand_k",     # or "fall_back" or "skip_refinement"
    )
    docs = gated.get_relevant_documents("What is X?")

The default `on_low_coherence="expand_k"` doubles k and re-retrieves
when coherence is below threshold (the "low coherence = need broader
context" remediation). Other strategies are documented inline.
"""

from __future__ import annotations

from typing import Any, List, Literal, Optional

import numpy as np

try:
    from langchain.callbacks.manager import CallbackManagerForRetrieverRun
    from langchain.schema import BaseRetriever, Document
    from langchain.embeddings.base import Embeddings
except ImportError as exc:               # pragma: no cover
    raise ImportError(
        "langchain is required for this integration. "
        "Install with: pip install langchain"
    ) from exc


def _ccs(embeddings: List[List[float]]) -> float:
    """Same formula as src.ccs_gate_retriever — kept inline so this file
    is a self-contained drop-in for the upstream PR."""
    if len(embeddings) < 2:
        return 1.0
    E = np.asarray(embeddings, dtype=np.float64)
    norm = np.linalg.norm(E, axis=1, keepdims=True) + 1e-12
    En = E / norm
    sims = En @ En.T
    iu = np.triu_indices(len(sims), k=1)
    pair = sims[iu]
    return float(pair.mean() - pair.std())


class CoherenceGatedRetriever(BaseRetriever):
    """A retriever that gates on Context Coherence Score (CCS).

    Wraps any LangChain ``BaseRetriever``. After the wrapped retriever
    returns documents, we compute CCS over the document embeddings; if
    CCS < ``ccs_threshold`` the policy specified in ``on_low_coherence``
    is invoked. Otherwise the documents are returned unchanged.

    Parameters
    ----------
    base_retriever : BaseRetriever
        The underlying retriever to wrap (e.g. a Chroma or FAISS retriever).
    embeddings : Embeddings
        The embedder used to score CCS. Should match the one used by
        ``base_retriever`` for consistency.
    ccs_threshold : float, default 0.5
        Gate fires when CCS < this. Empirically tuned in Maganti (2026).
    on_low_coherence : str, default "expand_k"
        Remediation strategy when the gate fires:
          - "expand_k"        : double k and re-retrieve (default)
          - "fall_back"       : return an empty list (downstream handles
                                 zero-shot fallback)
          - "skip_refinement" : just return the original docs
                                 (use this if the only follow-on step
                                  is per-passage refinement, which the
                                  paradox tells us to skip on low CCS)
    log_decisions : bool, default False
        If True, attach a ``ccs_decision`` dict to each returned
        Document's metadata for downstream observability.
    """

    base_retriever: BaseRetriever
    embeddings:     Embeddings
    ccs_threshold:  float = 0.5
    on_low_coherence: Literal["expand_k", "fall_back", "skip_refinement"] = "expand_k"
    log_decisions:  bool = False

    class Config:
        arbitrary_types_allowed = True

    # ── BaseRetriever API ─────────────────────────────────────────────

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        docs = self.base_retriever.get_relevant_documents(
            query, callbacks=run_manager.get_child(),
        )
        return self._apply_gate(query, docs, run_manager)

    async def _aget_relevant_documents(
        self, query: str, *, run_manager,
    ) -> List[Document]:
        docs = await self.base_retriever.aget_relevant_documents(
            query, callbacks=run_manager.get_child(),
        )
        return self._apply_gate(query, docs, run_manager)

    # ── Gate logic ─────────────────────────────────────────────────────

    def _apply_gate(self, query, docs, run_manager) -> List[Document]:
        if len(docs) < 2:
            return docs

        embs = self.embeddings.embed_documents([d.page_content for d in docs])
        ccs = _ccs(embs)
        fires = ccs < self.ccs_threshold
        decision = {
            "ccs":           round(ccs, 4),
            "threshold":     self.ccs_threshold,
            "fires":         fires,
            "policy":        self.on_low_coherence,
        }

        if not fires:
            if self.log_decisions:
                for d in docs:
                    d.metadata["ccs_decision"] = decision
            return docs

        # Gate fired — apply the remediation
        if self.on_low_coherence == "fall_back":
            return []
        if self.on_low_coherence == "skip_refinement":
            return docs

        # "expand_k": double k and re-retrieve
        original_k = getattr(self.base_retriever, "search_kwargs", {}).get("k")
        if original_k is None:
            return docs
        # Best-effort: most LangChain retrievers support search_kwargs={"k": ...}
        try:
            self.base_retriever.search_kwargs["k"] = original_k * 2
            expanded = self.base_retriever.get_relevant_documents(
                query, callbacks=run_manager.get_child(),
            )
        finally:
            self.base_retriever.search_kwargs["k"] = original_k

        if self.log_decisions:
            decision["expanded_k"] = original_k * 2
            for d in expanded:
                d.metadata["ccs_decision"] = decision
        return expanded
