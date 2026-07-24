"""CCSGate — turn CCS into a single-line deployment decision.

Usage::

    from context_coherence import CCSGate

    gate = CCSGate(threshold=0.5)
    if gate.fires(retrieved_docs, embedder=my_st):
        # Coherence is below threshold — re-retrieve / fall back / expand-k
        ...
    else:
        # Set is coherent enough; ship to generator
        ...

The class is deliberately minimal: one threshold, one decision. For the
full HCPC-v$2$ retriever (with rank-protection + sub-chunk merge-back)
see the companion repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Union

from .core import ccs_from_embeddings, ccs_from_texts


@dataclass
class CCSGate:
    """Coherence-based decision policy.

    Attributes
    ----------
    threshold : tau in [-1, 1]
        Gate fires when CCS(set) < tau. Default 0.5 matches the
        empirically-tuned operating point in Maganti (2026).
    """

    threshold: float = 0.5

    def __post_init__(self):
        if not (-1.0 <= self.threshold <= 1.0):
            raise ValueError(
                f"threshold must be in [-1, 1], got {self.threshold}"
            )

    def score(self, items, embedder=None) -> float:
        """Return CCS for the given items.

        `items` is either a 2D embedding array or a list of strings;
        in the latter case `embedder` must be provided (see
        :func:`context_coherence.ccs`).
        """
        from .core import ccs as _ccs
        return _ccs(items, embedder=embedder)

    def fires(self, items, embedder=None) -> bool:
        """True if CCS < threshold (i.e., set is incoherent enough to
        warrant intervention)."""
        return self.score(items, embedder=embedder) < self.threshold

    def decision(self, items, embedder=None) -> dict:
        """Full decision payload — useful for logging.

        Returns
        -------
        dict with keys: ccs (float), threshold (float), fires (bool).
        """
        s = self.score(items, embedder=embedder)
        return {
            "ccs":       s,
            "threshold": self.threshold,
            "fires":     s < self.threshold,
        }
