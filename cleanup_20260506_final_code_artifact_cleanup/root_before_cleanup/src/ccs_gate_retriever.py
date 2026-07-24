"""
src/ccs_gate_retriever.py — Phase 4 #4 (CCS-as-policy reframe)
==============================================================

A deliberately *simpler* retriever than HCPC-v2 that exposes a single
decision policy:

    if CCS(retrieved set) >= tau:
        # Coherent set — do NOT refine (refinement would break it)
        return baseline_set
    else:
        # Incoherent set — refine all (like HCPC-v1)
        return refined_set

This isolates the **CCS gate** from HCPC-v2's other moving parts
(rank-protected top-k, dual-threshold AND, sub-chunk merge-back). If
this stripped-down policy still recovers most of the HCPC-v2 gain, the
gate itself --- not the protection mechanism --- is the active
ingredient. If HCPC-v2 still wins meaningfully, the protection rule
adds independent value.

The class deliberately mirrors `HCPCRetriever` and `HCPCv2Retriever`'s
`.retrieve(query) -> (docs, log)` signature so the same evaluation
harness picks it up without modification.

Usage:
    from src.ccs_gate_retriever import CCSGateRetriever
    retriever = CCSGateRetriever(pipeline=pipe, ccs_threshold=0.55)
    docs, log = retriever.retrieve("What is X?")
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ── Defaults derived from results/coherence_analysis/condition_summary.csv ────
# Median CCS across the multidataset run is ~0.50. We pick a threshold
# slightly below that so the gate fires when coherence is *materially*
# below the typical retrieval set, not on every below-median query.
DEFAULT_CCS_THRESHOLD = 0.50
DEFAULT_TOP_K         = 3


@dataclass
class CCSGateRetriever:
    """Coherence-gated retriever.

    Attributes
    ----------
    pipeline       : RAGPipeline (for retrieve_with_scores + embeddings)
    ccs_threshold  : tau in [0, 1]; gate fires when CCS < tau
    top_k          : final number of documents to return
    fallback       : "hcpc_v1" (refine all) or "baseline" (return raw)
                     selects what to do when the gate fires (CCS low).
                     "hcpc_v1" matches the original framing in the paper.
    """

    pipeline:      Any
    ccs_threshold: float = DEFAULT_CCS_THRESHOLD
    top_k:         int   = DEFAULT_TOP_K
    fallback:      str   = "hcpc_v1"     # alt: "baseline"

    def __post_init__(self) -> None:
        if self.fallback not in ("hcpc_v1", "baseline"):
            raise ValueError(
                f"fallback must be 'hcpc_v1' or 'baseline', "
                f"got {self.fallback!r}"
            )
        # Lazy-construct the v1 retriever only if we need it for fallback.
        self._hcpc_v1 = None
        if self.fallback == "hcpc_v1":
            from src.hcpc_retriever import HCPCRetriever
            self._hcpc_v1 = HCPCRetriever(
                pipeline=self.pipeline, top_k=self.top_k,
            )
        print(f"[CCSGate] tau={self.ccs_threshold}  fallback={self.fallback}")

    # ── Coherence ─────────────────────────────────────────────────────────

    def _compute_ccs(self, docs: List[Any]) -> float:
        """Mean pairwise cosine similarity − std, computed over the
        embeddings of the retrieved chunks. Identical formula to the one
        used by HCPCv2 to keep the diagnostic comparable."""
        if len(docs) < 2:
            return 1.0
        try:
            embs = self.pipeline.embeddings.embed_documents(
                [d.page_content for d in docs]
            )
        except Exception as exc:
            logger.warning("[CCSGate] embedding failed: %s", exc)
            return 0.0
        E = np.array(embs)
        norm = np.linalg.norm(E, axis=1, keepdims=True) + 1e-12
        E = E / norm
        sims = E @ E.T
        n = len(sims)
        # Off-diagonal pairwise sims
        iu = np.triu_indices(n, k=1)
        pair = sims[iu]
        return float(pair.mean() - pair.std())

    # ── Main API ─────────────────────────────────────────────────────────

    def retrieve(self, query: str) -> Tuple[List[Any], Dict]:
        # Coarse retrieval (same coarse step as everyone)
        raw_docs, sims = self.pipeline.retrieve_with_scores(query)
        if not raw_docs:
            return [], _empty_log(self.ccs_threshold)

        # Compute pre-refinement CCS — this is the *gate input*
        ccs = self._compute_ccs(raw_docs[: self.top_k])

        # Decision policy
        gate_fires = ccs < self.ccs_threshold

        if gate_fires:
            # Low coherence — fall back to chosen alternative
            if self.fallback == "hcpc_v1":
                docs, _v1_log = self._hcpc_v1.retrieve(query)
                # We deliberately only return v1's docs; we own the log.
            else:  # baseline
                docs = raw_docs[: self.top_k]
        else:
            # High coherence — preserve baseline (no refinement)
            docs = raw_docs[: self.top_k]

        # CCS of the *final* set (may differ from pre-CCS if v1 refined)
        ccs_final = self._compute_ccs(docs)

        log = {
            "refined":                   bool(gate_fires and self.fallback == "hcpc_v1"),
            "context_coherence":         round(ccs_final, 4),
            "ccs_pre":                   round(ccs, 4),
            "gate_fired":                bool(gate_fires),
            "ccs_threshold":             self.ccs_threshold,
            "fallback":                  self.fallback,
            "n_chunks_before":           len(raw_docs),
            "n_chunks_after":            len(docs),
            "mean_retrieval_similarity": round(
                float(np.mean([s for _d, s in zip(docs, sims[: len(docs)])]))
                if docs else 0.0, 4,
            ),
        }
        return docs, log


def _empty_log(tau: float) -> Dict:
    return {
        "refined":                   False,
        "context_coherence":         1.0,
        "ccs_pre":                   1.0,
        "gate_fired":                False,
        "ccs_threshold":             tau,
        "fallback":                  "hcpc_v1",
        "n_chunks_before":           0,
        "n_chunks_after":            0,
        "mean_retrieval_similarity": 0.0,
    }
