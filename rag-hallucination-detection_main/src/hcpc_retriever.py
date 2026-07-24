"""
Hybrid Context-Preserving Chunking (HCPC) Retriever
====================================================

HCPC is a two-stage retrieval strategy that starts with large 1024-token
chunks (for broad context capture) and dynamically refines *only* the chunks
that are too weak to reliably ground the generator.

Stage 1 — Coarse retrieval
  • Index documents with fixed 1024-token chunks (same as baseline).
  • Retrieve top-k chunks using standard cosine similarity search.

Stage 2 — Selective refinement
  • Score every retrieved chunk on two axes:
      (a) Cosine similarity to the query (vector-store score).
      (b) Cross-encoder relevance score (NLI-proxy via ms-marco).
  • A chunk is "weak" if EITHER score falls below its threshold.
  • Weak chunks are sub-split into ~256-token pieces.
  • Sub-chunks are re-ranked by cross-encoder to pick the single best slice
    that is most relevant to the query.
  • The refined sub-chunk replaces the weak parent in the final context.

Final context
  • Strong original chunks  +  best sub-chunk per weak parent
  • If total > top_k, a final cross-encoder pass re-ranks and truncates.

Logging (per query)
  • n_strong, n_weak, n_refined
  • Per-refinement: original text preview, original scores, n sub-chunks
    produced, best sub-chunk CE score, CE improvement delta.

Usage
-----
    from src.hcpc_retriever import HCPCRetriever

    hcpc = HCPCRetriever(pipeline)                      # default thresholds
    docs, log = hcpc.retrieve(query)                    # returns (docs, log)
    result = pipeline.generate(query, docs)             # normal generation
"""

from __future__ import annotations

import re
from typing import Any, Optional

import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder


# ── Default hyper-parameters ──────────────────────────────────────────────────

DEFAULT_SIM_THRESHOLD  = 0.50   # cosine similarity below → weak
DEFAULT_CE_THRESHOLD   = 0.00   # cross-encoder logit below → weak (ms-marco raw logits)
DEFAULT_SUB_CHUNK_SIZE = 256    # tokens for sub-splitting weak chunks
DEFAULT_SUB_OVERLAP    = 32     # token overlap for sub-splits
DEFAULT_TOP_K          = 3      # final context size


# ── Helper ────────────────────────────────────────────────────────────────────

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ── Core class ────────────────────────────────────────────────────────────────

class HCPCRetriever:
    """
    Two-stage Hybrid Context-Preserving Chunking retriever.

    Parameters
    ----------
    pipeline : RAGPipeline
        A fully initialised pipeline whose vectorstore is already built from
        1024-token fixed chunks.  The retriever borrows ``pipeline.embeddings``
        for sub-chunk re-embedding without reloading the model.
    sim_threshold : float
        Cosine-similarity threshold (0–1).  Chunks below this are weak.
    ce_threshold : float
        Cross-encoder raw logit threshold.  Chunks below this are weak.
        The ms-marco CE model outputs raw logits (no sigmoid); a value of 0.0
        is a neutral boundary.
    sub_chunk_size : int
        Target token size for sub-splits (≈ 4 chars/token).
    sub_chunk_overlap : int
        Overlap in tokens for sub-splits.
    top_k : int
        Number of chunks in the final context returned to the generator.
    ce_model_name : str
        HuggingFace cross-encoder model for relevance scoring.
    """

    STRATEGY = "hcpc"

    def __init__(
        self,
        pipeline: Any,
        sim_threshold: float = DEFAULT_SIM_THRESHOLD,
        ce_threshold: float  = DEFAULT_CE_THRESHOLD,
        sub_chunk_size: int  = DEFAULT_SUB_CHUNK_SIZE,
        sub_chunk_overlap: int = DEFAULT_SUB_OVERLAP,
        top_k: int           = DEFAULT_TOP_K,
        ce_model_name: str   = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        self.pipeline        = pipeline
        self.sim_threshold   = sim_threshold
        self.ce_threshold    = ce_threshold
        self.sub_chunk_size  = sub_chunk_size
        self.sub_chunk_overlap = sub_chunk_overlap
        self.top_k           = top_k

        print(f"[HCPC] Loading cross-encoder: {ce_model_name}")
        self.cross_encoder = CrossEncoder(ce_model_name)

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=sub_chunk_size,
            chunk_overlap=sub_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        print(f"[HCPC] Ready  "
              f"(sim_thr={sim_threshold}, ce_thr={ce_threshold}, "
              f"sub_chunk={sub_chunk_size}tok)")

    # ── Public API ────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
    ) -> tuple[list[Document], dict]:
        """
        Two-stage HCPC retrieval.

        Returns
        -------
        (docs, log)
            docs : final list of Documents to pass to the generator
            log  : dict with keys
                     n_strong, n_weak, n_refined,
                     strong_sims, weak_sims,
                     refinements (list of per-chunk dicts)
        """
        # ── Stage 1: coarse retrieval ─────────────────────────────────────────
        raw_docs, sim_scores = self.pipeline.retrieve_with_scores(query)

        if not raw_docs:
            return [], {"n_strong": 0, "n_weak": 0, "n_refined": 0, "refinements": []}

        # Cross-encoder relevance (NLI-proxy) for every coarse chunk
        ce_inputs  = [(query, doc.page_content[:512]) for doc in raw_docs]
        ce_scores  = self._safe_ce_predict(ce_inputs)

        # ── Classify chunks: strong vs. weak ─────────────────────────────────
        strong_docs: list[Document] = []
        weak_items:  list[tuple[Document, float, float]] = []   # (doc, sim, ce)

        for doc, sim, ce in zip(raw_docs, sim_scores, ce_scores):
            is_weak = (sim < self.sim_threshold) or (ce < self.ce_threshold)
            if is_weak:
                weak_items.append((doc, sim, ce))
            else:
                doc.metadata["hcpc_stage"]  = "strong"
                doc.metadata["hcpc_sim"]    = round(sim, 4)
                doc.metadata["hcpc_ce"]     = round(float(ce), 4)
                strong_docs.append(doc)

        # ── Stage 2: selective refinement ─────────────────────────────────────
        refined_docs: list[Document] = []
        refinements:  list[dict]     = []

        for parent_doc, parent_sim, parent_ce in weak_items:
            best_sub, ref_entry = self._refine_chunk(
                query, parent_doc, parent_sim, float(parent_ce)
            )
            if best_sub is not None:
                refined_docs.append(best_sub)
            refinements.append(ref_entry)

        # ── Merge + final truncation ──────────────────────────────────────────
        merged = strong_docs + refined_docs

        if len(merged) > self.top_k:
            merged = self._final_rerank(query, merged)

        log: dict = {
            "n_strong": len(strong_docs),
            "n_weak":   len(weak_items),
            "n_refined": len(refined_docs),
            "strong_sims": [round(s, 4) for s in sim_scores[:len(strong_docs)]],
            "weak_sims":   [round(s, 4) for _, s, _ in weak_items],
            "refinements": refinements,
        }

        return merged, log

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _refine_chunk(
        self,
        query: str,
        parent_doc: Document,
        parent_sim: float,
        parent_ce: float,
    ) -> tuple[Optional[Document], dict]:
        """
        Sub-split a weak parent chunk and pick the best sub-chunk.

        Returns (best_sub_doc, log_entry).
        If sub-splitting yields nothing useful, returns (None, log_entry).
        """
        text = parent_doc.page_content

        # Sub-split
        sub_docs = self._splitter.create_documents(
            [text],
            metadatas=[{
                **parent_doc.metadata,
                "hcpc_stage":      "sub_chunk",
                "hcpc_parent_sim": round(parent_sim, 4),
                "hcpc_parent_ce":  round(parent_ce, 4),
            }],
        )

        if not sub_docs:
            return None, _empty_ref(parent_doc, parent_sim, parent_ce, reason="no_sub_chunks")

        # Re-score sub-chunks with cross-encoder (fast, CPU-friendly)
        ce_inputs  = [(query, sd.page_content[:512]) for sd in sub_docs]
        sub_ce     = self._safe_ce_predict(ce_inputs)

        # Also compute cosine similarity for the best sub-chunk selection
        best_sub, best_sim, best_ce_val = self._pick_best_by_similarity(
            query, sub_docs, sub_ce
        )

        if best_sub is None:
            return None, _empty_ref(parent_doc, parent_sim, parent_ce, reason="embed_failed")

        best_sub.metadata["hcpc_sub_sim"]  = round(best_sim, 4)
        best_sub.metadata["hcpc_sub_ce"]   = round(best_ce_val, 4)

        ref_entry = {
            "parent_preview":   text[:120].replace("\n", " "),
            "parent_sim":       round(parent_sim, 4),
            "parent_ce":        round(parent_ce, 4),
            "n_sub_chunks":     len(sub_docs),
            "best_sub_preview": best_sub.page_content[:80].replace("\n", " "),
            "best_sub_sim":     round(best_sim, 4),
            "best_sub_ce":      round(best_ce_val, 4),
            "sim_improvement":  round(best_sim - parent_sim, 4),
            "ce_improvement":   round(best_ce_val - parent_ce, 4),
        }

        return best_sub, ref_entry

    def _pick_best_by_similarity(
        self,
        query: str,
        sub_docs: list[Document],
        sub_ce_scores: list[float],
    ) -> tuple[Optional[Document], float, float]:
        """
        Embed sub-chunk texts in-memory and return the sub-chunk with the
        highest cosine similarity to the query.

        Returns (best_doc, best_sim, best_ce_score).
        """
        try:
            query_emb  = np.array(
                self.pipeline.embeddings.embed_query(query), dtype=np.float32
            )
            sub_texts  = [sd.page_content for sd in sub_docs]
            sub_embs   = np.array(
                self.pipeline.embeddings.embed_documents(sub_texts), dtype=np.float32
            )

            sims     = np.array([_cosine(query_emb, e) for e in sub_embs])
            best_idx = int(np.argmax(sims))
            return sub_docs[best_idx], float(sims[best_idx]), float(sub_ce_scores[best_idx])

        except Exception as exc:
            print(f"[HCPC] Sub-chunk embedding failed ({exc}); falling back to CE only.")
            # Fallback: pick best by cross-encoder score
            if sub_ce_scores:
                best_idx = int(np.argmax(sub_ce_scores))
                return sub_docs[best_idx], 0.0, float(sub_ce_scores[best_idx])
            return None, 0.0, 0.0

    def _final_rerank(self, query: str, docs: list[Document]) -> list[Document]:
        """Final cross-encoder pass to select the best top_k from merged pool."""
        if len(docs) <= self.top_k:
            return docs
        pairs   = [(query, doc.page_content[:512]) for doc in docs]
        scores  = self._safe_ce_predict(pairs)
        ranked  = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
        return [doc for _, doc in ranked[: self.top_k]]

    def _safe_ce_predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        """Cross-encoder predict with graceful error handling."""
        if not pairs:
            return []
        try:
            return [float(s) for s in self.cross_encoder.predict(pairs)]
        except Exception as exc:
            print(f"[HCPC] Cross-encoder predict failed ({exc}); using 0.0.")
            return [0.0] * len(pairs)

    # ── Diagnostics ───────────────────────────────────────────────────────────

    def summary_stats(self, logs: list[dict]) -> dict:
        """
        Aggregate HCPC log entries across multiple queries.

        Parameters
        ----------
        logs : list of per-query log dicts returned by retrieve()

        Returns
        -------
        dict with keys:
            n_queries, mean_n_weak, pct_queries_with_refinement,
            mean_ce_improvement, mean_sim_improvement
        """
        if not logs:
            return {}

        n = len(logs)
        n_weak_per_query = [l["n_weak"] for l in logs]
        queries_with_ref = sum(1 for l in logs if l["n_weak"] > 0)

        ce_deltas: list[float] = []
        sim_deltas: list[float] = []
        for l in logs:
            for ref in l.get("refinements", []):
                ce_deltas.append(ref.get("ce_improvement", 0.0))
                sim_deltas.append(ref.get("sim_improvement", 0.0))

        result: dict = {
            "n_queries":                  n,
            "mean_n_weak_per_query":      round(sum(n_weak_per_query) / n, 3),
            "pct_queries_with_refinement": round(queries_with_ref / n, 4),
        }
        if ce_deltas:
            result["mean_ce_improvement"]  = round(sum(ce_deltas) / len(ce_deltas), 4)
        if sim_deltas:
            result["mean_sim_improvement"] = round(sum(sim_deltas) / len(sim_deltas), 4)

        return result


# ── Private helpers ───────────────────────────────────────────────────────────

def _empty_ref(doc: Document, sim: float, ce: float, reason: str) -> dict:
    return {
        "parent_preview": doc.page_content[:120].replace("\n", " "),
        "parent_sim":     round(sim, 4),
        "parent_ce":      round(ce, 4),
        "n_sub_chunks":   0,
        "reason":         reason,
        "best_sub_preview": "",
        "best_sub_sim":   0.0,
        "best_sub_ce":    0.0,
        "sim_improvement": 0.0,
        "ce_improvement":  0.0,
    }
