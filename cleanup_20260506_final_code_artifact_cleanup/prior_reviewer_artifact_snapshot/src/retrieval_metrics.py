"""
Retrieval Quality Metrics

Measures how well the top-k retrieved chunks relate to the query using
embedding cosine similarity. These metrics are logged alongside hallucination
scores to help separate retrieval failure from generation failure.

Exported function
-----------------
compute_retrieval_quality(query, docs, embeddings) -> dict

Keys returned
-------------
mean_similarity   : average cosine similarity across all retrieved docs
max_similarity    : closest retrieved doc to the query
min_similarity    : most distant retrieved doc
relevance_spread  : max - min (high spread = heterogeneous top-k)
n_docs            : number of docs evaluated
"""

from __future__ import annotations

from typing import Any

import numpy as np
from langchain_core.documents import Document


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ── Main function ─────────────────────────────────────────────────────────────

def compute_retrieval_quality(
    query: str,
    docs: list[Document],
    embeddings: Any,
    max_chars_per_doc: int = 512,
) -> dict:
    """
    Compute cosine-similarity-based retrieval quality for a single query.

    Parameters
    ----------
    query             : the question string
    docs              : list of retrieved LangChain Documents
    embeddings        : LangChain-compatible embeddings (embed_query + embed_documents)
    max_chars_per_doc : truncation limit per doc to keep embedding fast

    Returns
    -------
    dict with keys:
        mean_similarity, max_similarity, min_similarity,
        relevance_spread, n_docs
    All similarity values are in [-1, 1]; -1.0 signals a computation error.
    """
    _empty = {
        "mean_similarity": 0.0,
        "max_similarity": 0.0,
        "min_similarity": 0.0,
        "relevance_spread": 0.0,
        "n_docs": 0,
    }

    if not docs:
        return _empty

    try:
        query_emb = np.array(embeddings.embed_query(query), dtype=np.float32)

        doc_texts = [doc.page_content[:max_chars_per_doc] for doc in docs]
        doc_embs = [
            np.array(e, dtype=np.float32)
            for e in embeddings.embed_documents(doc_texts)
        ]

        sims = [_cosine(query_emb, de) for de in doc_embs]

        return {
            "mean_similarity": round(float(np.mean(sims)), 4),
            "max_similarity": round(float(np.max(sims)), 4),
            "min_similarity": round(float(np.min(sims)), 4),
            "relevance_spread": round(float(np.max(sims) - np.min(sims)), 4),
            "n_docs": len(docs),
        }

    except Exception as exc:
        print(f"[RetrievalMetrics] Warning: metric computation failed — {exc}")
        return {
            "mean_similarity": -1.0,
            "max_similarity": -1.0,
            "min_similarity": -1.0,
            "relevance_spread": -1.0,
            "n_docs": len(docs),
        }
