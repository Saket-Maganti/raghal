"""Tests for CCS computation and the bare CCS-gate retriever."""

from __future__ import annotations

import numpy as np
import pytest

from src.ccs_gate_retriever import CCSGateRetriever, _empty_log


def _make_docs(texts, doc_cls):
    return [doc_cls(t) for t in texts]


# ── CCS math ──────────────────────────────────────────────────────────

def test_ccs_single_doc_returns_one(fake_pipeline, fake_doc):
    """Single doc → CCS undefined; the implementation returns 1.0."""
    r = CCSGateRetriever(pipeline=fake_pipeline)
    assert r._compute_ccs(_make_docs(["only one"], fake_doc)) == 1.0


def test_ccs_in_unit_interval(fake_pipeline, fake_doc):
    r = CCSGateRetriever(pipeline=fake_pipeline)
    docs = _make_docs([
        "the cat sat on the mat",
        "a dog barks loudly",
        "quantum mechanics describes nature",
        "the mat had a cat on it",
    ], fake_doc)
    ccs = r._compute_ccs(docs)
    # Mean cosine ∈ [-1, 1]; std ≥ 0; so CCS = mean − std ∈ [-1, 1]
    assert -1.0 <= ccs <= 1.0


def test_ccs_higher_for_repeated_text(fake_pipeline, fake_doc):
    r = CCSGateRetriever(pipeline=fake_pipeline)
    similar = _make_docs(["foo bar baz"] * 4, fake_doc)
    diverse = _make_docs(["foo", "wholly different", "x y z", "lorem ipsum"], fake_doc)
    assert r._compute_ccs(similar) > r._compute_ccs(diverse)


# ── Gate decision ─────────────────────────────────────────────────────

def test_gate_fires_on_low_coherence(fake_pipeline, fake_doc):
    r = CCSGateRetriever(pipeline=fake_pipeline,
                          ccs_threshold=0.95, fallback="baseline")
    # Force the pipeline to return diverse docs (will have low CCS)
    docs = _make_docs(["a", "b", "c"], fake_doc)
    fake_pipeline.retrieve_with_scores.return_value = (docs, [0.5, 0.5, 0.5])
    out_docs, log = r.retrieve("q")
    assert log["gate_fired"] is True
    assert len(out_docs) == 3


def test_gate_skips_on_high_coherence(fake_pipeline, fake_doc):
    r = CCSGateRetriever(pipeline=fake_pipeline,
                          ccs_threshold=-1.0, fallback="baseline")
    docs = _make_docs(["a", "b", "c"], fake_doc)
    fake_pipeline.retrieve_with_scores.return_value = (docs, [0.5, 0.5, 0.5])
    out_docs, log = r.retrieve("q")
    assert log["gate_fired"] is False


def test_empty_retrieval_returns_empty(fake_pipeline):
    r = CCSGateRetriever(pipeline=fake_pipeline, fallback="baseline")
    fake_pipeline.retrieve_with_scores.return_value = ([], [])
    docs, log = r.retrieve("q")
    assert docs == []
    assert log["n_chunks_after"] == 0


def test_invalid_fallback_raises(fake_pipeline):
    with pytest.raises(ValueError):
        CCSGateRetriever(pipeline=fake_pipeline, fallback="nonsense")


def test_log_keys_present(fake_pipeline, fake_doc):
    r = CCSGateRetriever(pipeline=fake_pipeline, fallback="baseline")
    docs = _make_docs(["a", "b"], fake_doc)
    fake_pipeline.retrieve_with_scores.return_value = (docs, [0.5, 0.5])
    _, log = r.retrieve("q")
    expected = {"refined", "context_coherence", "ccs_pre", "gate_fired",
                "ccs_threshold", "fallback", "n_chunks_before",
                "n_chunks_after", "mean_retrieval_similarity"}
    assert expected.issubset(set(log.keys()))


def test_empty_log_has_full_schema():
    log = _empty_log(0.5)
    expected = {"refined", "context_coherence", "ccs_pre", "gate_fired",
                "ccs_threshold", "fallback", "n_chunks_before",
                "n_chunks_after", "mean_retrieval_similarity"}
    assert expected.issubset(set(log.keys()))
    assert log["ccs_threshold"] == 0.5
