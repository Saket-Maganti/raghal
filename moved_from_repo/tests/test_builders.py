"""Tests for the figure/table builders that auto-generate paper artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _run(script: str) -> subprocess.CompletedProcess:
    """Run an experiments/builder and return the result for assertions."""
    return subprocess.run(
        ["python3", script], cwd=ROOT, capture_output=True, text=True,
    )


# ── Headline figure (Phase 3 #1) ─────────────────────────────────────

def test_headline_figure_builds():
    r = _run("experiments/build_headline_figure.py")
    assert r.returncode == 0, r.stderr[-500:]
    assert (ROOT / "ragpaper/figures/headline_frontier.pdf").exists()
    assert (ROOT / "ragpaper/figures/headline_frontier.tex").exists()


# ── CCS calibration figure (Phase 3 #7) ──────────────────────────────

def test_ccs_calibration_builds():
    r = _run("experiments/build_ccs_calibration.py")
    assert r.returncode == 0, r.stderr[-500:]
    pdf = ROOT / "ragpaper/figures/ccs_calibration.pdf"
    assert pdf.exists() and pdf.stat().st_size > 1000

    csv = ROOT / "results/ccs_calibration/quintile_table.csv"
    assert csv.exists()
    df = pd.read_csv(csv)
    assert {"halluc_rate", "ccs_mean", "n"}.issubset(df.columns)


# ── Disentanglement figure (Phase 4 #2) ──────────────────────────────

def test_disentanglement_figure_builds():
    r = _run("experiments/build_disentanglement_figure.py")
    assert r.returncode == 0, r.stderr[-500:]
    assert (ROOT / "ragpaper/figures/disentanglement.pdf").exists()
    df = pd.read_csv(ROOT / "results/disentanglement/quartile_table.csv")
    assert "faith_mean" in df.columns
    assert len(df) >= 4   # at least 1 row per sim quartile


# ── Top-k table builder (Phase 4 #1) ─────────────────────────────────

def test_topk_table_builder_skips_when_no_data(tmp_path, monkeypatch):
    """If paradox_by_k.csv is missing, builder should fail with a clear error."""
    monkeypatch.chdir(tmp_path)
    # Run from a clean dir where no inputs exist
    r = subprocess.run(
        ["python3", str(ROOT / "experiments/build_topk_table.py")],
        capture_output=True, text=True,
    )
    # Either succeeds (if there's pre-existing CSV) or exits with a clear msg
    if r.returncode != 0:
        assert "missing" in (r.stdout + r.stderr).lower()


def test_topk_table_populates_when_data_present():
    """If we have paradox_by_k.csv, the builder produces a non-stub fragment."""
    csv = ROOT / "results/topk_sensitivity/paradox_by_k.csv"
    if not csv.exists():
        pytest.skip("top-k results not yet present")
    r = _run("experiments/build_topk_table.py")
    assert r.returncode == 0
    out = (ROOT / "ragpaper/figures/topk_table.tex").read_text()
    assert "populated after" not in out      # placeholder language
    assert "paradox" in out.lower() or "$" in out
