"""
src/mmr_retriever.py — MMR (Maximal Marginal Relevance) baseline retriever.

A standard diversification baseline used widely in IR. Used in Phase 7
to compare against HCPC-v2 head-to-head: MMR also tries to balance
relevance and diversity, but does so via a per-passage greedy
trade-off rather than via a coherence gate.

MMR(D, k, λ) — iteratively pick documents:
    next = argmax_{d ∉ S} [λ · sim(d, q) − (1−λ) · max_{d'∈S} sim(d, d')]

λ = 1.0 reduces to greedy top-k by query similarity (= baseline).
λ = 0.5 (our default) balances relevance + diversity equally.
λ = 0.0 picks the most novel document, ignoring query relevance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple

import numpy as np


@dataclass
class MMRRetriever:
    """MMR diversification on top of a base RAGPipeline.

    Pulls top-`pool_size` candidates from the underlying retriever,
    then re-selects `top_k` via MMR with parameter `lambda_`.
    """

    pipeline:   Any
    lambda_:    float = 0.5
    top_k:      int   = 3
    pool_size:  int   = 20

    def __post_init__(self):
        if not (0.0 <= self.lambda_ <= 1.0):
            raise ValueError(f"lambda_ must be in [0, 1], got {self.lambda_}")
        print(f"[MMR] lambda={self.lambda_}  k={self.top_k}  "
              f"pool_size={self.pool_size}")

    def _embed(self, texts: List[str]) -> np.ndarray:
        return np.asarray(self.pipeline.embeddings.embed_documents(list(texts)))

    def _embed_query(self, q: str) -> np.ndarray:
        return np.asarray(self.pipeline.embeddings.embed_query(q))

    def retrieve(self, query: str) -> Tuple[List[Any], dict]:
        # Step 1: pull a wider pool from the base retriever.
        original_k = getattr(self.pipeline, "top_k", self.top_k)
        try:
            self.pipeline.top_k = self.pool_size
            cands, sims = self.pipeline.retrieve_with_scores(query)
        finally:
            self.pipeline.top_k = original_k

        if not cands:
            return [], _empty_log(self.lambda_)
        if len(cands) <= self.top_k:
            return cands, {"refined": False, "lambda": self.lambda_,
                           "n_chunks_before": len(cands),
                           "n_chunks_after": len(cands),
                           "mean_retrieval_similarity":
                                round(float(np.mean(sims)) if sims else 0.0, 4),
                           "context_coherence": -1.0}

        # Step 2: embed query + candidates
        q_emb = self._embed_query(query)
        c_embs = self._embed([c.page_content for c in cands])
        # Normalise
        q_n = q_emb / (np.linalg.norm(q_emb) + 1e-12)
        c_n = c_embs / (np.linalg.norm(c_embs, axis=1, keepdims=True) + 1e-12)
        # Pre-compute query relevance and pairwise sims
        rel = c_n @ q_n
        pair = c_n @ c_n.T

        # Step 3: greedy MMR selection
        selected: List[int] = []
        remaining = list(range(len(cands)))
        # Seed with the highest-relevance candidate
        seed = int(np.argmax(rel))
        selected.append(seed)
        remaining.remove(seed)

        while len(selected) < self.top_k and remaining:
            # max diversity penalty over already-selected
            max_sim_to_sel = pair[remaining][:, selected].max(axis=1)
            score = self.lambda_ * rel[remaining] - (1 - self.lambda_) * max_sim_to_sel
            pick = remaining[int(np.argmax(score))]
            selected.append(pick)
            remaining.remove(pick)

        chosen = [cands[i] for i in selected]
        chosen_sims = [sims[i] for i in selected] if sims else []

        log = {
            "refined":                   True,    # MMR always rewrites the set
            "lambda":                    self.lambda_,
            "n_chunks_before":           len(cands),
            "n_chunks_after":            len(chosen),
            "mean_retrieval_similarity": round(
                float(np.mean(chosen_sims)) if chosen_sims else 0.0, 4),
            "context_coherence":         _ccs_from_embeddings(c_embs[selected]),
        }
        return chosen, log


def _ccs_from_embeddings(E: np.ndarray) -> float:
    if len(E) < 2: return 1.0
    Ev = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-12)
    sims = Ev @ Ev.T
    iu = np.triu_indices(len(sims), k=1)
    pair = sims[iu]
    return round(float(pair.mean() - pair.std()), 4)


def _empty_log(lam: float) -> dict:
    return {
        "refined": False, "lambda": lam,
        "n_chunks_before": 0, "n_chunks_after": 0,
        "mean_retrieval_similarity": 0.0,
        "context_coherence": 1.0,
    }
