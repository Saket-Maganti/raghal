"""Pure-numpy core of the Context Coherence Score.

CCS(C) = mean(off-diag pairwise cosine sim) − std(off-diag pairwise cosine sim)

Intuition: a coherent set has *consistently high* pairwise similarity;
both the mean and the std matter. A set with high mean but high variance
(two tight sub-clusters) is less useful than one with a moderate mean
and low variance (everything in one mid-similarity cloud).
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Optional, Sequence, Union

import numpy as np

ArrayLike = Union[np.ndarray, Sequence[Sequence[float]]]


# ── Public API ────────────────────────────────────────────────────────

def ccs(embeddings_or_texts, embedder=None) -> float:
    """Convenience dispatcher.

    - If `embeddings_or_texts` is a numpy/2D array → treat as embeddings.
    - If it's a list of strings → require `embedder` and embed first.

    Returns CCS in [-1, 1]; near 1 = coherent, near 0 = scattered.
    """
    if isinstance(embeddings_or_texts, np.ndarray):
        return ccs_from_embeddings(embeddings_or_texts)
    if hasattr(embeddings_or_texts, "__len__") and len(embeddings_or_texts) > 0:
        first = embeddings_or_texts[0]
        if isinstance(first, str):
            if embedder is None:
                raise ValueError(
                    "Pass `embedder=` when ccs() is called on raw strings. "
                    "Either a sentence-transformers SentenceTransformer or "
                    "any callable f(list[str]) -> np.ndarray."
                )
            return ccs_from_texts(embeddings_or_texts, embedder)
        # Assume a 2D iterable of floats
        return ccs_from_embeddings(np.asarray(embeddings_or_texts))
    raise ValueError("ccs() requires non-empty embeddings or texts")


def ccs_from_embeddings(E: ArrayLike) -> float:
    """Compute CCS from an (n, d) embedding matrix.

    Embeddings are L2-normalised before cosine similarity is computed,
    so callers can pass either normalised or raw vectors.
    """
    E = np.asarray(E, dtype=np.float64)
    if E.ndim != 2:
        raise ValueError(f"embeddings must be (n, d), got shape {E.shape}")
    n = E.shape[0]
    if n < 2:
        # Single passage is trivially coherent.
        return 1.0
    norm = np.linalg.norm(E, axis=1, keepdims=True) + 1e-12
    En = E / norm
    sims = En @ En.T
    iu = np.triu_indices(n, k=1)
    pair = sims[iu]
    return float(pair.mean() - pair.std())


def ccs_from_texts(
    texts: Sequence[str],
    embedder: Union[Callable[[Sequence[str]], np.ndarray], "SentenceTransformer"],
) -> float:
    """Embed `texts` and compute CCS.

    `embedder` is either:
      - a `sentence_transformers.SentenceTransformer` (uses .encode), or
      - any callable that takes list[str] and returns an (n, d) array.
    """
    if hasattr(embedder, "encode"):
        E = embedder.encode(list(texts), normalize_embeddings=True)
    elif callable(embedder):
        E = embedder(list(texts))
    else:
        raise TypeError(
            "embedder must have .encode() or be callable; "
            f"got {type(embedder).__name__}"
        )
    return ccs_from_embeddings(np.asarray(E))
