"""context_coherence — Context Coherence Score (CCS) for RAG.

Quick start
-----------
    from context_coherence import ccs, CCSGate

    # Plain CCS over already-embedded chunks
    score = ccs(embeddings)             # numpy (n, d) array

    # Or over text using your favourite embedder
    score = ccs.from_texts(["passage 1", "passage 2", ...],
                            embedder=my_st_model)

    # As a deployment-time decision
    gate = CCSGate(threshold=0.5)
    if gate.fires(passages_or_embeddings):
        # Coherent set — pass to generator unmodified
        ...
    else:
        # Incoherent — re-retrieve / expand-k / fall back to zero-shot
        ...

The package is intentionally small and dependency-light: pure-numpy core,
embedders are pluggable. Install with `pip install context-coherence`.
"""

from .core import ccs, ccs_from_embeddings, ccs_from_texts
from .gate import CCSGate

__version__ = "0.2.0"
__all__ = [
    "ccs",
    "ccs_from_embeddings",
    "ccs_from_texts",
    "CCSGate",
    "__version__",
]
