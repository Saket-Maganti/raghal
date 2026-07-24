"""
HCPC-Selective v2 (Hybrid Context-Preserving Chunking)
=======================================================

Improvements over v1:
  1. Dual-threshold weak detection   (sim AND ce, not OR)
  2. Top-k protection gate           (never refine top-N ranked chunks)
  3. Refinement cap                  (max_refine, pick lowest-sim candidates)
  4. Merge-back strategy             (restore semantic continuity post-split)
  5. Context budget control          (max_final_chunks = top_k)
  6. Context Coherence Score (CCS)   (mean cosine sim between adjacent chunks)
  7. Rich per-query diagnostics

Weak detection rule (AND, not OR):
    weak = (sim < sim_threshold) AND (ce < ce_threshold)

This is stricter than v1's OR condition, preventing over-refinement of
chunks that are strong on at least one axis.

Usage
-----
    from src.hcpc_v2_retriever import HCPCv2Retriever

    hcpc_v2 = HCPCv2Retriever(pipeline)
    docs, log = hcpc_v2.retrieve(query)
    result    = pipeline.generate(query, docs)
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Tuple

import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

# ── Default hyper-parameters ──────────────────────────────────────────────────

DEFAULT_SIM_THRESHOLD   = 0.45   # chunk weak if BELOW this (AND ce also weak)
DEFAULT_CE_THRESHOLD    = -0.20  # cross-encoder logit weak if BELOW this
DEFAULT_TOP_K_PROTECTED = 2      # top-N ranked chunks are never refined
DEFAULT_MAX_REFINE      = 2      # max weak chunks refined per query
DEFAULT_SUB_CHUNK_SIZE  = 256    # sub-split token target
DEFAULT_SUB_OVERLAP     = 32     # sub-split token overlap
MERGE_MAX_CHARS         = 1024 * 4   # ≈1024 tokens for merge-back check

# Adaptive thresholding defaults
DEFAULT_THRESHOLD_MODE  = "fixed"  # "fixed" | "adaptive"
DEFAULT_SIM_PERCENTILE  = 60       # percentile of sim scores used as sim_threshold
DEFAULT_CE_PERCENTILE   = 40       # percentile of CE scores used as ce_threshold
ADAPTIVE_MIN_CHUNKS     = 2        # min chunks required to compute adaptive threshold


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ── Core class ────────────────────────────────────────────────────────────────

class HCPCv2Retriever:
    """
    HCPC-Selective v2: context-aware selective refinement retriever.

    Parameters
    ----------
    pipeline : RAGPipeline
        Fully initialised pipeline with 1024-token indexed chunks.
        Borrows ``pipeline.embeddings`` to avoid model reloads.
    sim_threshold : float
        Cosine similarity threshold.  Chunk is weak if BELOW this
        AND ce score is also below ce_threshold (AND gate).
    ce_threshold : float
        Cross-encoder logit threshold.  ms-marco outputs raw logits;
        -0.2 is a conservative weak boundary.
    top_k_protected : int
        Top-N chunks by retrieval rank that are NEVER refined.
    max_refine : int
        Maximum weak chunks to refine per query.  Excess candidates are
        dropped (lowest-similarity first kept).
    sub_chunk_size : int
        Sub-split target in tokens (~4 chars per token).
    sub_chunk_overlap : int
        Sub-split overlap in tokens.
    ce_model_name : str
        HuggingFace cross-encoder model identifier.
    """

    STRATEGY = "hcpc_v2"

    def __init__(
        self,
        pipeline: Any,
        sim_threshold: float   = DEFAULT_SIM_THRESHOLD,
        ce_threshold: float    = DEFAULT_CE_THRESHOLD,
        top_k_protected: int   = DEFAULT_TOP_K_PROTECTED,
        max_refine: int        = DEFAULT_MAX_REFINE,
        sub_chunk_size: int    = DEFAULT_SUB_CHUNK_SIZE,
        sub_chunk_overlap: int = DEFAULT_SUB_OVERLAP,
        ce_model_name: str     = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        # ── Adaptive thresholding (new) ────────────────────────────────────
        threshold_mode: str    = DEFAULT_THRESHOLD_MODE,
        sim_percentile: int    = DEFAULT_SIM_PERCENTILE,
        ce_percentile: int     = DEFAULT_CE_PERCENTILE,
    ):
        self.pipeline          = pipeline
        self.sim_threshold     = sim_threshold
        self.ce_threshold      = ce_threshold
        self.top_k_protected   = top_k_protected
        self.max_refine        = max_refine
        self.sub_chunk_size    = sub_chunk_size
        self.sub_chunk_overlap = sub_chunk_overlap
        self.top_k             = pipeline.top_k   # context budget
        # Adaptive thresholding state
        self.threshold_mode    = threshold_mode
        self.sim_percentile    = sim_percentile
        self.ce_percentile     = ce_percentile

        print(f"[HCPCv2] Loading cross-encoder: {ce_model_name}")
        self._ce = CrossEncoder(ce_model_name)

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=sub_chunk_size,
            chunk_overlap=sub_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        # Reuse the pipeline's already-loaded embedding model
        self._embeddings = pipeline.embeddings

        if threshold_mode == "adaptive":
            print(
                f"[HCPCv2] Ready  "
                f"(mode=adaptive, sim_pct={sim_percentile}, ce_pct={ce_percentile}, "
                f"top_k_protected={top_k_protected}, max_refine={max_refine}, "
                f"sub_chunk={sub_chunk_size}tok)"
            )
        else:
            print(
                f"[HCPCv2] Ready  "
                f"(sim_thr={sim_threshold}, ce_thr={ce_threshold}, "
                f"top_k_protected={top_k_protected}, max_refine={max_refine}, "
                f"sub_chunk={sub_chunk_size}tok)"
            )

    # ── Threshold resolution ──────────────────────────────────────────────────

    def _resolve_thresholds(
        self,
        sims: List[float],
        ce_scores: List[float],
    ) -> Tuple[float, float]:
        """
        Return (eff_sim_threshold, eff_ce_threshold) for this query.

        fixed mode   — returns stored sim_threshold / ce_threshold unchanged.
        adaptive mode — computes thresholds as percentiles of the retrieved
                        chunk scores.  Falls back to fixed if insufficient
                        data (< ADAPTIVE_MIN_CHUNKS).

        Percentile semantics
        --------------------
        sim_percentile=60 means: flag chunks whose sim is below the 60th
        percentile of the current retrieval pool — so the bottom ~40% are
        eligible for refinement.

        ce_percentile=40 means: flag chunks whose CE score is below the 40th
        percentile — the bottom ~60% by CE are eligible.

        Using already-available scores avoids any model re-execution.
        """
        if (
            self.threshold_mode == "adaptive"
            and len(sims) >= ADAPTIVE_MIN_CHUNKS
            and len(ce_scores) >= ADAPTIVE_MIN_CHUNKS
        ):
            eff_sim = float(np.percentile(sims, self.sim_percentile))
            eff_ce  = float(np.percentile(ce_scores, self.ce_percentile))
            return eff_sim, eff_ce

        # fixed mode or insufficient data
        return self.sim_threshold, self.ce_threshold

    # ── Public API ────────────────────────────────────────────────────────────

    def retrieve(self, query: str) -> Tuple[List[Document], dict]:
        """
        HCPC-Selective v2 two-stage retrieval.

        Returns
        -------
        (docs, log)
            docs : final ranked Documents for the generator (len ≤ top_k)
            log  : per-query diagnostic dict (see _empty_log for keys)
        """
        # ── Stage 1: coarse retrieval ─────────────────────────────────────────
        raw_docs, sims = self.pipeline.retrieve_with_scores(query)

        if not raw_docs:
            return [], _empty_log()

        n_before        = len(raw_docs)
        best_sim_before = float(max(sims))

        # CE scores for all coarsely retrieved chunks (batch)
        ce_scores      = self._safe_ce_predict(
            [(query, d.page_content[:512]) for d in raw_docs]
        )
        best_ce_before = float(max(ce_scores)) if ce_scores else 0.0

        # ── Resolve thresholds (adaptive uses per-query percentiles) ──────────
        eff_sim_thr, eff_ce_thr = self._resolve_thresholds(sims, ce_scores)

        # ── Classify: protected / strong / candidate-weak ─────────────────────
        # rank 0 = best cosine match from vectorstore
        protected_entries: List[Tuple[int, Document, float, float]] = []
        strong_entries:    List[Tuple[int, Document, float, float]] = []
        candidate_weak:    List[Tuple[int, Document, float, float]] = []

        for rank, (doc, sim, ce) in enumerate(zip(raw_docs, sims, ce_scores)):
            entry = (rank, doc, float(sim), float(ce))
            if rank < self.top_k_protected:
                # Protected by rank gate — never refined
                protected_entries.append(entry)
            elif (sim < eff_sim_thr) and (ce < eff_ce_thr):
                # Dual-threshold AND gate: both axes must be weak
                candidate_weak.append(entry)
            else:
                strong_entries.append(entry)

        # ── Refinement cap: keep at most max_refine lowest-sim chunks ─────────
        if len(candidate_weak) > self.max_refine:
            candidate_weak.sort(key=lambda x: x[2])   # ascending by sim
            candidate_weak = candidate_weak[: self.max_refine]

        refined   = bool(candidate_weak)
        n_refined = len(candidate_weak)

        # ── Stage 2: selective refinement with merge-back ─────────────────────
        refined_entries: List[Tuple[int, Document, float, float]] = []
        n_merged = 0

        for rank, doc, _parent_sim, _parent_ce in candidate_weak:
            sub_docs            = self._sub_split(doc, rank)
            merged_subs, n_m    = self._merge_adjacent(sub_docs)
            n_merged           += n_m
            best_doc, best_sim, best_ce = self._pick_best(query, merged_subs)
            refined_entries.append((rank, best_doc, best_sim, best_ce))

        # ── Combine + sort by original rank ───────────────────────────────────
        all_entries = protected_entries + strong_entries + refined_entries
        all_entries.sort(key=lambda x: x[0])

        # ── Context budget: keep top_k ────────────────────────────────────────
        if len(all_entries) > self.top_k:
            all_entries = all_entries[: self.top_k]

        final_docs = [d for _, d, _, _ in all_entries]
        final_sims = [s for _, _, s, _ in all_entries]
        final_ces  = [c for _, _, _, c in all_entries]

        best_sim_after = float(max(final_sims)) if final_sims else 0.0
        best_ce_after  = float(max(final_ces))  if final_ces  else 0.0

        # ── Context Coherence Score (reuses embedding model, no reload) ───────
        ccs = self._compute_ccs(final_docs)

        # ── Approximate context token count (chars ÷ 4) ───────────────────────
        context_token_count = sum(len(d.page_content) for d in final_docs) // 4

        log = {
            "refined":                   refined,
            "n_chunks_before":           n_before,
            "n_chunks_after":            len(final_docs),
            "n_refined_chunks":          n_refined,
            "n_merged_chunks":           n_merged,
            "best_sim_before":           round(best_sim_before, 4),
            "best_sim_after":            round(best_sim_after,  4),
            "best_ce_before":            round(best_ce_before,  4),
            "best_ce_after":             round(best_ce_after,   4),
            "context_coherence":         round(ccs, 4),
            "context_token_count":       context_token_count,
            "mean_retrieval_similarity": round(
                float(np.mean(final_sims)) if final_sims else 0.0, 4
            ),
            # ── Threshold diagnostics (new) ────────────────────────────────
            "threshold_mode":            self.threshold_mode,
            "eff_sim_threshold":         round(eff_sim_thr, 4),
            "eff_ce_threshold":          round(eff_ce_thr,  4),
            "sim_percentile":            self.sim_percentile if self.threshold_mode == "adaptive" else -1,
            "ce_percentile":             self.ce_percentile  if self.threshold_mode == "adaptive" else -1,
        }
        return final_docs, log

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _sub_split(self, doc: Document, parent_rank: int) -> List[Document]:
        """
        Sub-split a weak chunk into smaller pieces, tagging each with
        parent rank and sequential position for merge-back tracking.
        """
        sub_texts = self._splitter.split_text(doc.page_content)
        if not sub_texts:
            return [doc]
        result = []
        for i, text in enumerate(sub_texts):
            meta = dict(doc.metadata)
            meta["hcpc_v2_parent_rank"]  = parent_rank
            meta["hcpc_v2_sub_position"] = i
            meta["hcpc_v2_stage"]        = "sub_chunk"
            result.append(Document(page_content=text, metadata=meta))
        return result

    def _merge_adjacent(
        self, sub_docs: List[Document]
    ) -> Tuple[List[Document], int]:
        """
        Merge adjacent sub-chunks from the same parent to restore semantic
        continuity, provided they are contiguous and their combined length
        does not exceed MERGE_MAX_CHARS (≈1024 tokens).

        Returns (merged_docs, n_merges_performed).
        """
        if len(sub_docs) <= 1:
            return sub_docs, 0

        merged: List[Document] = []
        buffer = sub_docs[0]
        n_merges = 0

        for nxt in sub_docs[1:]:
            buf_pos     = buffer.metadata.get("hcpc_v2_sub_position", -1)
            nxt_pos     = nxt.metadata.get("hcpc_v2_sub_position", -1)
            same_parent = (
                buffer.metadata.get("hcpc_v2_parent_rank")
                == nxt.metadata.get("hcpc_v2_parent_rank")
            )
            contiguous   = same_parent and (nxt_pos == buf_pos + 1)
            combined_len = len(buffer.page_content) + len(nxt.page_content)

            if contiguous and combined_len <= MERGE_MAX_CHARS:
                meta = dict(buffer.metadata)
                meta["hcpc_v2_sub_position"] = nxt_pos   # advance position
                buffer = Document(
                    page_content=buffer.page_content + " " + nxt.page_content,
                    metadata=meta,
                )
                n_merges += 1
            else:
                merged.append(buffer)
                buffer = nxt

        merged.append(buffer)
        return merged, n_merges

    def _pick_best(
        self,
        query: str,
        sub_docs: List[Document],
    ) -> Tuple[Document, float, float]:
        """
        Select the best sub-chunk by cosine similarity to query.
        Falls back to CE-only ranking if embedding fails.

        Returns (best_doc, best_sim, best_ce).
        """
        if not sub_docs:
            return Document(page_content="", metadata={}), 0.0, 0.0

        if len(sub_docs) == 1:
            try:
                emb_q = np.array(
                    self._embeddings.embed_query(query), dtype=np.float32
                )
                emb_d = np.array(
                    self._embeddings.embed_documents([sub_docs[0].page_content])[0],
                    dtype=np.float32,
                )
                sim = _cosine(emb_q, emb_d)
                ce  = float(
                    self._ce.predict([(query, sub_docs[0].page_content[:512])])[0]
                )
                return sub_docs[0], float(sim), ce
            except Exception as exc:
                logger.warning("[HCPCv2] single pick fallback: %s", exc)
                return sub_docs[0], 0.0, 0.0

        # Multi-doc: embed all sub-chunks then argmax cosine similarity
        try:
            texts  = [d.page_content for d in sub_docs]
            emb_q  = np.array(
                self._embeddings.embed_query(query), dtype=np.float32
            )
            emb_ds = np.array(
                self._embeddings.embed_documents(texts), dtype=np.float32
            )
            sims      = np.array([_cosine(emb_q, e) for e in emb_ds])
            ce_scores = self._safe_ce_predict(
                [(query, t[:512]) for t in texts]
            )
            best_idx = int(np.argmax(sims))
            return (
                sub_docs[best_idx],
                float(sims[best_idx]),
                float(ce_scores[best_idx]),
            )
        except Exception as exc:
            logger.warning("[HCPCv2] multi-doc embedding failed: %s", exc)

        # CE-only fallback
        try:
            texts     = [d.page_content for d in sub_docs]
            ce_scores = self._safe_ce_predict(
                [(query, t[:512]) for t in texts]
            )
            best_idx = int(np.argmax(ce_scores))
            return sub_docs[best_idx], 0.0, float(ce_scores[best_idx])
        except Exception:
            return sub_docs[0], 0.0, 0.0

    def _compute_ccs(self, docs: List[Document]) -> float:
        """
        Context Coherence Score: mean(all_pairwise_sims) - std(all_pairwise_sims).

        Why not mean alone?
        all-MiniLM-L6-v2 encodes same-document chunks into a tight cosine
        cluster (~0.85-0.95).  A plain mean is therefore near-constant across
        configs, making threshold sweeps uninterpretable.  Subtracting std
        penalises configs where coherence is *uneven* — some pairs very similar,
        others less so — rewarding uniformly coherent contexts.

        All pairwise pairs (not just adjacent) give a richer signal for k=3
        (3 pairs vs 2 adjacent pairs).

        Edge cases
        ----------
        Single doc   → return 0.0   (no pairwise signal; 1.0 would inflate score)
        Two docs     → one pair, std = 0 → return that cosine value
        Embed error  → return -1.0
        """
        if len(docs) <= 1:
            return 0.0
        try:
            texts = [d.page_content for d in docs]
            embs  = np.array(
                self._embeddings.embed_documents(texts), dtype=np.float32
            )
            n = len(embs)
            pair_sims = [
                _cosine(embs[i], embs[j])
                for i in range(n)
                for j in range(i + 1, n)
            ]
            if len(pair_sims) == 1:
                return round(float(pair_sims[0]), 4)
            mean_s = float(np.mean(pair_sims))
            std_s  = float(np.std(pair_sims))
            return round(mean_s - std_s, 4)
        except Exception as exc:
            logger.warning("[HCPCv2] CCS computation failed: %s", exc)
            return -1.0

    def _safe_ce_predict(
        self, pairs: List[Tuple[str, str]]
    ) -> List[float]:
        """Cross-encoder predict with graceful fallback to 0.0 on error."""
        if not pairs:
            return []
        try:
            return [float(s) for s in self._ce.predict(pairs)]
        except Exception as exc:
            logger.warning("[HCPCv2] CE predict failed: %s", exc)
            return [0.0] * len(pairs)

    # ── Diagnostics ───────────────────────────────────────────────────────────

    @staticmethod
    def summary_stats(logs: List[dict]) -> dict:
        """
        Aggregate per-query diagnostic logs into experiment-level statistics.

        Parameters
        ----------
        logs : list of per-query dicts returned by retrieve()

        Returns
        -------
        dict with keys: pct_queries_refined, mean_n_refined_per_query,
            mean_n_merged_per_query, mean_context_coherence,
            mean_sim_improvement, mean_ce_improvement
        """
        if not logs:
            return {}
        n                = len(logs)
        n_refined_queries = sum(1 for l in logs if l.get("refined"))
        mean_n_refined   = float(np.mean([l.get("n_refined_chunks", 0) for l in logs]))
        mean_n_merged    = float(np.mean([l.get("n_merged_chunks", 0) for l in logs]))

        ccs_vals = [
            l["context_coherence"]
            for l in logs
            if l.get("context_coherence", -1.0) >= 0.0
        ]
        mean_ccs = float(np.mean(ccs_vals)) if ccs_vals else 0.0

        sim_imps = [
            l["best_sim_after"] - l["best_sim_before"]
            for l in logs
            if l.get("refined")
        ]
        ce_imps = [
            l["best_ce_after"] - l["best_ce_before"]
            for l in logs
            if l.get("refined")
        ]

        return {
            "pct_queries_refined":      round(n_refined_queries / n * 100, 2),
            "mean_n_refined_per_query": round(mean_n_refined, 3),
            "mean_n_merged_per_query":  round(mean_n_merged,  3),
            "mean_context_coherence":   round(mean_ccs, 4),
            "mean_sim_improvement":     round(float(np.mean(sim_imps)) if sim_imps else 0.0, 4),
            "mean_ce_improvement":      round(float(np.mean(ce_imps))  if ce_imps  else 0.0, 4),
        }


# ── Private helpers ───────────────────────────────────────────────────────────

def _empty_log() -> dict:
    return {
        "refined":                   False,
        "n_chunks_before":           0,
        "n_chunks_after":            0,
        "n_refined_chunks":          0,
        "n_merged_chunks":           0,
        "best_sim_before":           0.0,
        "best_sim_after":            0.0,
        "best_ce_before":            0.0,
        "best_ce_after":             0.0,
        "context_coherence":         1.0,
        "context_token_count":       0,
        "mean_retrieval_similarity": 0.0,
    }
