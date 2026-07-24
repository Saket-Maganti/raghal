"""Shared pytest fixtures.

Keeps tests fast: we mock the heavy bits (Ollama, embedder downloads)
unless a test is explicitly marked as `@pytest.mark.integration`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def fake_doc():
    """Cheap stand-in for langchain Document with .page_content."""
    class _Doc:
        def __init__(self, text: str):
            self.page_content = text
            self.metadata = {}
    return _Doc


@pytest.fixture
def fake_embedder():
    """Returns deterministic 8-dim embeddings keyed off text hash so two
    similar strings produce similar vectors. Lets tests assert CCS bounds
    without loading sentence-transformers."""
    import numpy as np

    def _embed_documents(texts):
        out = []
        for t in texts:
            # Hash → 8 deterministic floats in [-1, 1]
            h = abs(hash(t)) % (10 ** 9)
            rng = np.random.default_rng(h)
            v = rng.standard_normal(8)
            v /= np.linalg.norm(v) + 1e-12
            out.append(v.tolist())
        return out

    e = MagicMock()
    e.embed_documents.side_effect = _embed_documents
    return e


@pytest.fixture
def fake_pipeline(fake_embedder):
    """Stub RAGPipeline with just .embeddings + .retrieve_with_scores."""
    p = MagicMock()
    p.embeddings = fake_embedder
    p.top_k = 3
    return p
