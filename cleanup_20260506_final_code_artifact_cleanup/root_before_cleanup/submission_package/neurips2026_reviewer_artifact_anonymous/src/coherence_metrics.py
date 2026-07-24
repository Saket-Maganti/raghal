"""
src/coherence_metrics.py
Metrics that measure *why* context coherence correlates with faithfulness.

Five complementary signals, all computed per-query over the ordered list of
retrieved passages:

1. semantic_continuity  — mean cosine similarity between adjacent chunks
                          (identical to CCS; included for cross-checking)
2. embedding_variance   — variance of cosine similarities among all chunk
                          pairs; low variance = uniform relevance
3. jaccard_similarity   — mean token-level Jaccard overlap between adjacent
                          chunks; measures lexical bridging
4. retrieval_entropy    — Shannon entropy of the cosine-similarity distribution
                          across retrieved chunks; high entropy = diverse retrieval
5. nli_pairwise_contradict — mean probability of NLI-contradiction across all
                          chunk pairs; captures stance/semantic conflict that
                          embedding-space sim can mask (introduced for the
                          adversarial evaluation in §7.6).

The first four are returned by compute_coherence_metrics(); the NLI-pairwise
signal is opt-in via compute_nli_pairwise() because it requires an NLI model.

Usage
-----
    from src.coherence_metrics import compute_coherence_metrics

    metrics = compute_coherence_metrics(query, docs, embeddings)
    # metrics["ccs"], metrics["semantic_continuity"], ...
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List

import numpy as np
from langchain_core.documents import Document


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _tokenize(text: str) -> set:
    """Lowercase word-token set, stripping punctuation."""
    return set(re.findall(r"\b\w+\b", text.lower()))


def _jaccard(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def _entropy(values: List[float]) -> float:
    """Shannon entropy of a list treated as an unnormalized distribution."""
    arr = np.array(values, dtype=float)
    # Shift to be non-negative before normalizing
    arr = arr - arr.min() + 1e-10
    arr = arr / arr.sum()
    return float(-np.sum(arr * np.log(arr + 1e-10)))


# ──────────────────────────────────────────────────────────────────────────────
# Main function
# ──────────────────────────────────────────────────────────────────────────────

def compute_coherence_metrics(
    query: str,
    docs: List[Document],
    embeddings: Any,          # LangChain embeddings object with .embed_documents()
    max_chars_per_doc: int = 1024,
) -> Dict[str, float]:
    """
    Compute all four coherence metrics for a single query.

    Parameters
    ----------
    query : str
        The input query (used for query-to-chunk similarity in entropy).
    docs : List[Document]
        Ordered list of retrieved passages.
    embeddings : LangChain embeddings object
        Used to embed passages.  Must support .embed_documents(List[str]).
    max_chars_per_doc : int
        Truncation limit per passage before embedding (saves compute).

    Returns
    -------
    dict with keys:
        n_docs                  : int
        ccs                     : float   (mean adjacent cosine sim)
        semantic_continuity     : float   (same as CCS, explicit label)
        embedding_variance      : float   (variance across all pairwise sims)
        mean_jaccard            : float   (mean adjacent token-Jaccard)
        min_jaccard             : float
        max_jaccard             : float
        retrieval_entropy       : float   (entropy of query-chunk sim distribution)
        mean_query_chunk_sim    : float   (mean query-to-chunk cosine sim)
        sim_spread              : float   (max - min query-to-chunk sim)
    """
    result: Dict[str, float] = {
        "n_docs": len(docs),
        "ccs": -1.0,
        "ccs_mean": -1.0,   # raw pairwise mean (before std penalty)
        "ccs_std": -1.0,    # pairwise std (the spread penalty)
        "semantic_continuity": -1.0,
        "embedding_variance": -1.0,
        "mean_jaccard": -1.0,
        "min_jaccard": -1.0,
        "max_jaccard": -1.0,
        "retrieval_entropy": -1.0,
        "mean_query_chunk_sim": -1.0,
        "sim_spread": -1.0,
    }

    if not docs:
        return result

    # ── Embedding-based metrics ──────────────────────────────────────────
    try:
        texts = [d.page_content[:max_chars_per_doc] for d in docs]
        query_truncated = query[:max_chars_per_doc]

        all_texts = [query_truncated] + texts
        all_vecs = np.array(embeddings.embed_documents(all_texts), dtype=float)

        norms = np.linalg.norm(all_vecs, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-10)
        all_vecs_n = all_vecs / norms

        query_vec = all_vecs_n[0]
        chunk_vecs = all_vecs_n[1:]

        # 1. CCS / semantic_continuity — all-pairwise mean - std (anti-saturation)
        # Plain adjacent mean saturates near 1.0 for same-document chunks with
        # all-MiniLM-L6-v2.  mean - std creates meaningful spread: coherent contexts
        # have low std (small penalty); fragmented ones have high std (larger penalty).
        if len(chunk_vecs) >= 2:
            n_cv = len(chunk_vecs)
            pair_sims = [
                float(chunk_vecs[i] @ chunk_vecs[j])
                for i in range(n_cv)
                for j in range(i + 1, n_cv)
            ]
            mean_s = float(np.mean(pair_sims))
            std_s  = float(np.std(pair_sims)) if len(pair_sims) > 1 else 0.0
            ccs    = mean_s - std_s
            result["ccs"]                = round(ccs,    4)
            result["semantic_continuity"] = round(ccs,   4)
            result["ccs_mean"]           = round(mean_s, 4)   # raw mean (for reference)
            result["ccs_std"]            = round(std_s,  4)   # spread penalty

        # 2. Embedding variance across all chunk pairs
        if len(chunk_vecs) >= 2:
            all_pair_sims = []
            for i in range(len(chunk_vecs)):
                for j in range(i + 1, len(chunk_vecs)):
                    all_pair_sims.append(float(chunk_vecs[i] @ chunk_vecs[j]))
            result["embedding_variance"] = round(float(np.var(all_pair_sims)), 4)

        # 3. Query-chunk similarities (used for entropy and spread)
        q_chunk_sims = [float(query_vec @ cv) for cv in chunk_vecs]
        result["mean_query_chunk_sim"] = round(float(np.mean(q_chunk_sims)), 4)
        result["sim_spread"] = round(float(np.max(q_chunk_sims) - np.min(q_chunk_sims)), 4)

        # 4. Retrieval entropy
        result["retrieval_entropy"] = round(_entropy(q_chunk_sims), 4)

    except Exception as exc:
        pass   # leave -1.0 defaults; logged by caller if needed

    # ── Lexical metrics (no embedding needed) ────────────────────────────
    try:
        token_sets = [_tokenize(d.page_content) for d in docs]
        if len(token_sets) >= 2:
            adj_jaccards = [
                _jaccard(token_sets[i], token_sets[i + 1])
                for i in range(len(token_sets) - 1)
            ]
            result["mean_jaccard"] = round(float(np.mean(adj_jaccards)), 4)
            result["min_jaccard"] = round(float(np.min(adj_jaccards)), 4)
            result["max_jaccard"] = round(float(np.max(adj_jaccards)), 4)
        elif len(token_sets) == 1:
            result["mean_jaccard"] = 1.0
            result["min_jaccard"] = 1.0
            result["max_jaccard"] = 1.0
    except Exception:
        pass

    return result


# ──────────────────────────────────────────────────────────────────────────────
# NLI-pairwise contradiction signal (for adversarial §7.6)
# ──────────────────────────────────────────────────────────────────────────────

def compute_nli_pairwise(
    docs: List[Document],
    nli_pipe: Any,
    max_chars_per_doc: int = 512,
) -> Dict[str, float]:
    """
    Pairwise NLI contradiction score over retrieved passages.

    For every unordered pair (d_i, d_j), run NLI(premise=d_i, hypothesis=d_j)
    and record P(contradiction). Return the mean, max, and proportion of pairs
    whose contradict-probability exceeds 0.5.

    Embedding-space cosine treats "X is effective" and "X is ineffective" as
    similar (same topic), so cosine-based CCS misses stance conflict. This
    metric complements CCS for the adversarial-contradictory case.

    Parameters
    ----------
    docs : ordered retrieved passages (len >= 2 for a meaningful signal).
    nli_pipe : a callable that accepts (premise, hypothesis) and returns a
               dict-like with key 'contradiction' in [0,1]. In the main
               pipeline this is a thin wrapper around HallucinationDetector.

    Returns
    -------
    dict with keys:
        nli_pairwise_mean     : mean contradiction probability across pairs
        nli_pairwise_max      : max contradiction probability across pairs
        nli_pairwise_frac_hi  : fraction of pairs with contradict > 0.5
        nli_pairs_evaluated   : number of ordered pairs evaluated
    """
    result = {
        "nli_pairwise_mean":    -1.0,
        "nli_pairwise_max":     -1.0,
        "nli_pairwise_frac_hi": -1.0,
        "nli_pairs_evaluated":  0,
    }
    if len(docs) < 2:
        return result

    probs: List[float] = []
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            p = docs[i].page_content[:max_chars_per_doc]
            h = docs[j].page_content[:max_chars_per_doc]
            try:
                scores = nli_pipe(p, h)
                c_prob = float(scores.get("contradiction", 0.0))
                probs.append(c_prob)
            except Exception:
                continue

    if not probs:
        return result

    result["nli_pairwise_mean"]    = round(float(np.mean(probs)), 4)
    result["nli_pairwise_max"]     = round(float(np.max(probs)),  4)
    result["nli_pairwise_frac_hi"] = round(
        float(sum(1 for p in probs if p > 0.5)) / len(probs), 4
    )
    result["nli_pairs_evaluated"]  = len(probs)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Correlation helper
# ──────────────────────────────────────────────────────────────────────────────

def correlations_with_faithfulness(
    records: List[Dict],
    metric_keys: List[str] | None = None,
    faithfulness_key: str = "faithfulness_score",
) -> Dict[str, Dict]:
    """
    Compute Spearman correlations between each coherence metric and faithfulness.

    Parameters
    ----------
    records : List[Dict]
        Each dict must contain faithfulness_key and the coherence metric keys.
    metric_keys : List[str] | None
        Which keys to correlate.  Defaults to all standard coherence metrics.
    faithfulness_key : str
        Column name for faithfulness score.

    Returns
    -------
    Dict mapping metric_name -> {"spearman_rho": float, "p_value": float, "n": int}
    """
    from scipy.stats import spearmanr

    if metric_keys is None:
        metric_keys = [
            "ccs",
            "semantic_continuity",
            "embedding_variance",
            "mean_jaccard",
            "retrieval_entropy",
            "mean_query_chunk_sim",
            "sim_spread",
        ]

    results = {}
    for key in metric_keys:
        pairs = [
            (r[key], r[faithfulness_key])
            for r in records
            if r.get(key, -1) >= 0 and faithfulness_key in r
        ]
        if len(pairs) < 4:
            results[key] = {"spearman_rho": None, "p_value": None, "n": len(pairs)}
            continue
        xs, ys = zip(*pairs)
        rho, pval = spearmanr(xs, ys)
        results[key] = {
            "spearman_rho": round(float(rho), 4),
            "p_value": round(float(pval), 4),
            "n": len(pairs),
        }
    return results
