"""
src/longform_metrics.py — Phase 2 Item 3 (long-form generation eval)
====================================================================

Metrics for evaluating multi-sentence (long-form) answers produced by a RAG
pipeline.  The short-answer NLI faithfulness used elsewhere in this repo
treats the answer as one span against the concatenated context; for
long-form answers that is too coarse because a single hallucinated claim
buried in 5 faithful claims still scores ≈ 0.8.

This module exposes three metric families:

    1. ROUGE-L       — classical long-form recall vs gold free-form answer.
    2. Per-claim NLI — split answer into sentences / clauses, score each
                       against the context; compute mean entailment and
                       fraction of unsupported claims.
    3. Length stats  — answer_token_count, answer_sentence_count.

All are pure-Python + no new deps beyond what the rest of the repo already
pulls in (torch / transformers / numpy).  ROUGE-L is implemented inline via
longest-common-subsequence to avoid adding `rouge-score` as a dependency
(some users hit tokenizer issues on old macOS).

Usage (in experiments/run_longform_eval.py):

    from src.longform_metrics import score_longform

    metrics = score_longform(
        answer="<string>",
        context="<string>",
        gold_answer="<string>",
        detector=<HallucinationDetector instance>,
    )
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


# ── Sentence splitting (lightweight, dependency-free) ────────────────────

_SENT_SPLIT_RE = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z0-9])"
    r"|(?<=[.!?])\n+"
    r"|\n{2,}"
)


def split_into_claims(text: str, min_len: int = 12) -> List[str]:
    """Split a long-form answer into sentence-like claims.

    Handles common post-processing junk (e.g. leading "Answer:",
    bullet markers).  Drops fragments shorter than `min_len` chars because
    very short sentences are usually headers or stop-phrases rather than
    atomic claims.
    """
    if not text:
        return []
    t = text.strip()
    # Strip leading metadata prefixes produced by CoT / expert templates.
    for prefix in ("Answer:", "Expert answer:", "Final answer:"):
        if t.lower().startswith(prefix.lower()):
            t = t[len(prefix):].strip()
    # Normalize bullets to newlines so the splitter sees them.
    t = re.sub(r"[\u2022\u2023\u25E6\u2043\u2219]", "\n", t)
    t = re.sub(r"^\s*[-*]\s+", "\n", t, flags=re.MULTILINE)

    parts = _SENT_SPLIT_RE.split(t)
    out: List[str] = []
    for p in parts:
        p = p.strip()
        if len(p) >= min_len:
            out.append(p)
    # Fall back to whole-text if splitting produced nothing.
    return out or ([t] if len(t) >= min_len else [])


# ── ROUGE-L (inline) ──────────────────────────────────────────────────────

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _tokens(s: str) -> List[str]:
    return [w.lower() for w in _WORD_RE.findall(s or "")]


def _lcs_length(a: List[str], b: List[str]) -> int:
    if not a or not b:
        return 0
    # Rolling-row DP to keep memory bounded on long answers.
    n, m = len(a), len(b)
    if n < m:
        a, b = b, a
        n, m = m, n
    prev = [0] * (m + 1)
    curr = [0] * (m + 1)
    for i in range(1, n + 1):
        ai = a[i - 1]
        for j in range(1, m + 1):
            if ai == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, prev
        for k in range(m + 1):
            curr[k] = 0
    return prev[m]


def rouge_l_f1(pred: str, gold: str) -> float:
    """Standard ROUGE-L F1 (β = 1) on token sequences."""
    p, g = _tokens(pred), _tokens(gold)
    if not p or not g:
        return 0.0
    lcs = _lcs_length(p, g)
    if lcs == 0:
        return 0.0
    precision = lcs / len(p)
    recall    = lcs / len(g)
    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


# ── Per-claim NLI faithfulness ────────────────────────────────────────────

def per_claim_faithfulness(
    claims: List[str],
    context: str,
    detector,
    supported_threshold: float = 0.5,
) -> Dict[str, float]:
    """Score each claim against the context; aggregate into answer-level.

    Returns:
        mean_claim_faith        — average per-claim NLI faithfulness
        min_claim_faith         — worst-case claim (useful for hallucination flag)
        unsupported_claim_rate  — fraction of claims below `supported_threshold`
        n_claims                — number of claims scored
    """
    if not claims:
        return {
            "mean_claim_faith":       0.0,
            "min_claim_faith":        0.0,
            "unsupported_claim_rate": 1.0,
            "n_claims":               0,
        }

    scores: List[float] = []
    for c in claims:
        try:
            out = detector.detect(c, context)
            scores.append(float(out.get("faithfulness_score", 0.0)))
        except Exception:
            scores.append(0.0)

    unsupported = sum(1 for s in scores if s < supported_threshold)
    return {
        "mean_claim_faith":       round(sum(scores) / len(scores), 4),
        "min_claim_faith":        round(min(scores), 4),
        "unsupported_claim_rate": round(unsupported / len(scores), 4),
        "n_claims":               len(scores),
    }


# ── Top-level scoring entry point ─────────────────────────────────────────

def score_longform(
    answer: str,
    context: str,
    gold_answer: str,
    detector,
    supported_threshold: float = 0.5,
) -> Dict[str, float]:
    """All long-form metrics for one (answer, context, gold) triple."""
    claims = split_into_claims(answer)
    claim_metrics = per_claim_faithfulness(
        claims, context, detector, supported_threshold
    )
    # Also compute the classic single-span faithfulness for backward
    # comparability with the short-answer tables.
    try:
        span_faith = float(detector.detect(answer, context)
                            .get("faithfulness_score", 0.0))
    except Exception:
        span_faith = 0.0

    answer_tokens    = _tokens(answer)
    gold_tokens      = _tokens(gold_answer)

    return {
        # length
        "answer_tokens":   len(answer_tokens),
        "gold_tokens":     len(gold_tokens),
        "n_claims":        claim_metrics["n_claims"],
        # ROUGE
        "rouge_l_f1":      rouge_l_f1(answer, gold_answer),
        # NLI (both aggregations)
        "span_faithfulness":       round(span_faith, 4),
        "mean_claim_faith":        claim_metrics["mean_claim_faith"],
        "min_claim_faith":         claim_metrics["min_claim_faith"],
        "unsupported_claim_rate":  claim_metrics["unsupported_claim_rate"],
        # Convenience booleans
        "is_hallucination_long":   claim_metrics["unsupported_claim_rate"] >= 0.3,
    }
