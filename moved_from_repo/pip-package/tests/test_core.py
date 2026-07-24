"""Tests for the standalone context-coherence package core."""

import numpy as np
import pytest

from context_coherence import CCSGate, ccs, ccs_from_embeddings, ccs_from_texts
from context_coherence.core import ccs as ccs_dispatcher


def test_ccs_single_embedding_returns_one():
    E = np.array([[1.0, 0.0, 0.0]])
    assert ccs_from_embeddings(E) == 1.0


def test_ccs_identical_embeddings_near_one():
    E = np.tile(np.array([1.0, 0.0, 0.0]), (5, 1))
    assert ccs_from_embeddings(E) == pytest.approx(1.0, abs=1e-6)


def test_ccs_orthogonal_embeddings_zero():
    E = np.eye(4)            # 4 orthogonal unit vectors → all off-diag = 0
    score = ccs_from_embeddings(E)
    # mean = 0, std = 0, so CCS = 0 exactly
    assert score == pytest.approx(0.0, abs=1e-9)


def test_ccs_in_unit_interval_with_random():
    rng = np.random.default_rng(42)
    E = rng.standard_normal((10, 32))
    score = ccs_from_embeddings(E)
    assert -1.0 <= score <= 1.0


def test_dispatcher_handles_embeddings():
    E = np.eye(3)
    assert ccs(E) == ccs_from_embeddings(E)


def test_dispatcher_requires_embedder_for_strings():
    with pytest.raises(ValueError):
        ccs(["a", "b", "c"])


def test_ccs_from_texts_with_callable_embedder():
    def fake_embed(texts):
        # Each text → a deterministic 4-vector based on length
        return np.array([[len(t) % 4, 1, 0, 0] for t in texts], dtype=float)
    score = ccs_from_texts(["a", "ab", "abc"], embedder=fake_embed)
    assert -1.0 <= score <= 1.0


def test_invalid_shape_raises():
    with pytest.raises(ValueError):
        ccs_from_embeddings(np.array([1.0, 2.0]))


# ── CCSGate ───────────────────────────────────────────────────────────

def test_gate_threshold_validation():
    with pytest.raises(ValueError):
        CCSGate(threshold=1.5)
    with pytest.raises(ValueError):
        CCSGate(threshold=-1.5)


def test_gate_fires_on_low_coherence():
    g = CCSGate(threshold=0.95)
    E = np.eye(3)            # CCS will be < 0.95
    assert g.fires(E) is True


def test_gate_doesnt_fire_on_high_coherence():
    g = CCSGate(threshold=0.0)
    E = np.tile(np.array([1.0, 0.0]), (3, 1))
    assert g.fires(E) is False


def test_gate_decision_payload():
    g = CCSGate(threshold=0.5)
    out = g.decision(np.eye(3))
    assert set(out.keys()) == {"ccs", "threshold", "fires"}
    assert isinstance(out["fires"], bool)
