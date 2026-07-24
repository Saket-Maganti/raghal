"""Tests for scripts/lint_paper.py — the gate that protects submission."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.lint_paper import (
    DOUBLE_WORD_RE,
    PERCENT_NO_ESCAPE_RE,
    PLACEHOLDER_RE,
    collect_bib_keys,
    strip_comments,
)


# ── Comment stripping ────────────────────────────────────────────────

def test_strip_comments_removes_line_comments():
    assert strip_comments("hello % comment").strip() == "hello"


def test_strip_comments_keeps_escaped_percent():
    out = strip_comments(r"value is 10\% high")
    assert "10\\%" in out


def test_strip_comments_preserves_non_comment_text():
    assert strip_comments("no comments here") == "no comments here"


# ── Regex sanity ─────────────────────────────────────────────────────

def test_placeholder_re_catches_todo():
    assert PLACEHOLDER_RE.search("TODO: write this")
    assert PLACEHOLDER_RE.search("FIXME later")
    assert PLACEHOLDER_RE.search("TBD here")
    assert PLACEHOLDER_RE.search("XXXX")
    assert not PLACEHOLDER_RE.search("This is fine.")


def test_double_word_re_catches_doubles():
    assert DOUBLE_WORD_RE.search("the the")
    assert DOUBLE_WORD_RE.search("of of")
    assert not DOUBLE_WORD_RE.search("the cat")


def test_percent_re_catches_unescaped():
    assert PERCENT_NO_ESCAPE_RE.search("10% growth")
    assert PERCENT_NO_ESCAPE_RE.search("0.5% loss")
    # Already-escaped → no match
    assert not PERCENT_NO_ESCAPE_RE.search("10\\% growth")


# ── Bib key collection ───────────────────────────────────────────────

def test_collect_bib_keys_handles_real_file(tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text(
        "@inproceedings{guu2020,\n  title={REALM},\n}\n"
        "@article{lewis2020,\n  title={RAG},\n}\n"
    )
    keys = collect_bib_keys(bib)
    assert keys == {"guu2020", "lewis2020"}


def test_collect_bib_keys_returns_empty_for_missing(tmp_path):
    assert collect_bib_keys(tmp_path / "nope.bib") == set()


# ── Integration: lint our own paper with 0 errors ────────────────────

def test_paper_lints_clean():
    """The paper itself must lint with 0 [ERR] issues."""
    import subprocess
    result = subprocess.run(
        ["python3", "scripts/lint_paper.py"],
        cwd=ROOT, capture_output=True, text=True,
    )
    last_line = (result.stdout or "").strip().splitlines()[-1]
    assert "0 errors" in last_line, f"lint not clean: {last_line!r}"
