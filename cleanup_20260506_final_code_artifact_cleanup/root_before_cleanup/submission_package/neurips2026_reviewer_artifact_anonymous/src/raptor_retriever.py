"""
src/raptor_retriever.py — Phase 2 Item 1 (baseline comparison)
==============================================================

A pragmatic, self-contained implementation of **RAPTOR** (Recursive
Abstractive Processing for Tree-Organized Retrieval, Sarthi et al. 2024).
Included as a *named* baseline against HCPC-v1/v2 in the head-to-head
table — reviewers expect this comparison and we should not wave it off.

What RAPTOR does, in one paragraph
----------------------------------
Split documents into leaf chunks → embed → cluster → summarise each
cluster with an LLM → treat those summaries as **new** chunks, re-embed,
cluster, summarise, etc., until one node remains.  At query time, retrieve
top-k over *all tree levels* so the generator can pick up both the fine
detail (leaves) and the overview (summaries).

What this file does
-------------------
We implement a **2-level** tree (leaves + one summary layer).  That is the
version that dominates the paper's released baseline (RAPTOR-Collapsed)
while keeping build time tractable on a laptop — a full recursive tree on
20-30 documents is overkill for our 30-question evaluations.

Interface contract
------------------
Same as `HCPCRetriever.retrieve`:
    docs, log = raptor.retrieve(query)
where `log` reports n_leaves, n_summaries, and which level each returned
chunk came from.  This lets `run_multidataset_validation.py` swap it in
with one line of wiring.

Dependencies
------------
sklearn (already pulled in transitively), numpy, RAGPipeline (for .llm and
.embeddings).  No new requirements.

Usage example
-------------
    from src.raptor_retriever import RAPTORRetriever

    pipeline = RAGPipeline(chunk_size=1024, ...)
    pipeline.index_documents(docs, collection_name="raptor_demo")

    raptor = RAPTORRetriever(pipeline, docs=docs, n_clusters=6)
    # Build summary layer lazily on first retrieve():
    docs_out, log = raptor.retrieve("What is X?")
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ── Default hyper-parameters ────────────────────────────────────────────────

DEFAULT_LEAF_CHUNK_SIZE = 1024
DEFAULT_LEAF_OVERLAP    = 100
DEFAULT_N_CLUSTERS      = 6     # for the summary layer.  6 ≈ sqrt(n_leaves) on
                                # a typical 30-paragraph corpus.
DEFAULT_TOP_K           = 3
DEFAULT_MIX_RATIO       = 0.5   # fraction of top-k allowed to come from leaves
                                # (remainder from summaries) — rounded up.
DEFAULT_MAX_SUM_WORDS   = 120

SUMMARY_PROMPT = (
    "Summarize the following passage in at most {max_words} words. "
    "Preserve named entities, numeric facts, and causal relations. "
    "Do not editorialize.\n\nPASSAGE:\n{text}\n\nSUMMARY:"
)


# ─────────────────────────────────────────────────────────────────────────────
# Clustering helpers
# ─────────────────────────────────────────────────────────────────────────────

def _cluster_embeddings(
    embs: np.ndarray, n_clusters: int, seed: int = 42,
) -> np.ndarray:
    """Return integer cluster id per row.

    Uses sklearn's AgglomerativeClustering (ward linkage) when n ≥ n_clusters,
    otherwise falls back to one-cluster-per-point so every chunk still gets
    an id.  Ward is the RAPTOR paper's default — they tried GMM too but ward
    was within noise on ablation.
    """
    from sklearn.cluster import AgglomerativeClustering
    n = len(embs)
    if n == 0:
        return np.array([], dtype=int)
    if n <= n_clusters:
        # Too few points to cluster — give each one its own summary cluster.
        return np.arange(n, dtype=int)
    model = AgglomerativeClustering(n_clusters=n_clusters, linkage="ward")
    return model.fit_predict(embs)


def _short_hash(text: str, n: int = 8) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:n]


# ─────────────────────────────────────────────────────────────────────────────
# Main class
# ─────────────────────────────────────────────────────────────────────────────

class RAPTORRetriever:
    """
    2-level RAPTOR (leaves + summary layer).

    The tree is built **lazily**: the first call to `.retrieve()` triggers
    leaf chunking, clustering, LLM summarisation, and embedding.  Subsequent
    calls reuse the cached tree.  That way we don't pay the build cost if a
    caller imports this class but uses a different retriever.

    Parameters
    ----------
    pipeline : RAGPipeline
        Provides the LLM (for summarisation) and the embeddings model
        (for re-embedding summaries).  We do NOT reuse pipeline.vectorstore
        directly — RAPTOR needs to keep summaries separable so we can tag
        results with their level.  Summaries live in an in-memory index.
    docs : list[Document]
        Source documents (pre-chunking).  Required on init so the tree is
        deterministic with respect to the caller's corpus.
    leaf_chunk_size / leaf_chunk_overlap : int
        Fixed splitter parameters for leaf chunks.
    n_clusters : int
        How many summary nodes to produce on the second layer.
    top_k : int
        Final context size returned to the generator.
    mix_ratio : float
        Fraction of `top_k` slots that can come from LEAF nodes.  If top_k=3
        and mix_ratio=0.5 we give 2 to leaves, 1 to summaries (ceil rounded).
    max_sum_words : int
        Word cap passed into the summarisation prompt.
    """

    STRATEGY = "raptor"

    def __init__(
        self,
        pipeline: Any,
        docs: List[Document],
        leaf_chunk_size: int = DEFAULT_LEAF_CHUNK_SIZE,
        leaf_chunk_overlap: int = DEFAULT_LEAF_OVERLAP,
        n_clusters: int = DEFAULT_N_CLUSTERS,
        top_k: int = DEFAULT_TOP_K,
        mix_ratio: float = DEFAULT_MIX_RATIO,
        max_sum_words: int = DEFAULT_MAX_SUM_WORDS,
    ):
        self.pipeline = pipeline
        self.docs = list(docs)
        self.leaf_chunk_size = leaf_chunk_size
        self.leaf_chunk_overlap = leaf_chunk_overlap
        self.n_clusters = n_clusters
        self.top_k = top_k
        self.mix_ratio = float(mix_ratio)
        self.max_sum_words = int(max_sum_words)

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=leaf_chunk_size,
            chunk_overlap=leaf_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # Tree state — populated lazily by _ensure_tree().
        self._built: bool = False
        self._leaves: List[Document] = []
        self._leaf_embs: Optional[np.ndarray] = None
        self._summaries: List[Document] = []
        self._sum_embs: Optional[np.ndarray] = None

        print(f"[RAPTOR] Configured (leaves={leaf_chunk_size}tok, "
              f"clusters={n_clusters}, top_k={top_k}, mix={mix_ratio})")

    # ── Tree build (lazy) ───────────────────────────────────────────────────

    def _ensure_tree(self) -> None:
        if self._built:
            return
        self._build_leaves()
        self._build_summary_layer()
        self._built = True

    def _build_leaves(self) -> None:
        print(f"[RAPTOR] Building leaf layer from {len(self.docs)} docs...")
        leaves = self._splitter.split_documents(self.docs)
        texts = [d.page_content for d in leaves]
        if not texts:
            self._leaves = []
            self._leaf_embs = np.zeros((0, 384), dtype=np.float32)
            return
        embs = np.asarray(
            self.pipeline.embeddings.embed_documents(texts),
            dtype=np.float32,
        )
        # Tag leaves with level + stable id so retrieval logs can reference them.
        for i, d in enumerate(leaves):
            d.metadata = dict(d.metadata or {})
            d.metadata.update({
                "raptor_level": "leaf",
                "raptor_id":    f"L0_{_short_hash(texts[i])}",
            })
        self._leaves = leaves
        self._leaf_embs = embs
        print(f"[RAPTOR] Leaves: {len(leaves)}")

    def _build_summary_layer(self) -> None:
        if not self._leaves:
            self._summaries = []
            self._sum_embs = np.zeros((0, 384), dtype=np.float32)
            return
        assert self._leaf_embs is not None
        labels = _cluster_embeddings(self._leaf_embs, self.n_clusters)
        cluster_to_leaves: Dict[int, List[int]] = {}
        for idx, lab in enumerate(labels):
            cluster_to_leaves.setdefault(int(lab), []).append(idx)

        summaries: List[Document] = []
        for cid, leaf_idxs in cluster_to_leaves.items():
            joined = "\n\n".join(self._leaves[i].page_content for i in leaf_idxs)
            prompt = SUMMARY_PROMPT.format(
                max_words=self.max_sum_words, text=joined[:8000]
            )
            try:
                summary_text = self.pipeline.llm.invoke(prompt)
            except Exception as exc:      # pragma: no cover — LLM flakiness
                print(f"[RAPTOR] summary LLM error (cluster {cid}): {exc}")
                # Fall back to a trivial lead-N summary so the tree stays whole.
                summary_text = " ".join(joined.split()[: self.max_sum_words])
            summary_text = (summary_text or "").strip()
            if not summary_text:
                summary_text = " ".join(joined.split()[: self.max_sum_words])
            meta = {
                "raptor_level":  "summary",
                "raptor_id":     f"L1_{cid}",
                "n_child_leaves": len(leaf_idxs),
                "child_leaf_ids": [self._leaves[i].metadata["raptor_id"]
                                   for i in leaf_idxs],
            }
            summaries.append(Document(page_content=summary_text, metadata=meta))

        sum_embs = np.asarray(
            self.pipeline.embeddings.embed_documents(
                [d.page_content for d in summaries]
            ),
            dtype=np.float32,
        )
        self._summaries = summaries
        self._sum_embs = sum_embs
        print(f"[RAPTOR] Summary layer: {len(summaries)} nodes "
              f"(mean {np.mean([m.metadata['n_child_leaves'] for m in summaries]):.1f} "
              f"leaves/cluster)")

    # ── Retrieval ───────────────────────────────────────────────────────────

    @staticmethod
    def _topk(query_emb: np.ndarray, node_embs: np.ndarray,
              k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Return (indices, similarities) for top-k cosine matches."""
        if len(node_embs) == 0 or k <= 0:
            return np.array([], dtype=int), np.array([], dtype=np.float32)
        # Normalise once.
        qn = query_emb / (np.linalg.norm(query_emb) + 1e-9)
        nn = node_embs / (np.linalg.norm(node_embs, axis=1, keepdims=True) + 1e-9)
        sims = nn @ qn
        k = min(k, len(node_embs))
        top = np.argpartition(-sims, k - 1)[:k]
        top = top[np.argsort(-sims[top])]
        return top, sims[top]

    def retrieve(self, query: str) -> Tuple[List[Document], Dict[str, Any]]:
        """Two-layer retrieval with per-level quotas.

        Returns (docs, log) where log carries counts and per-level ids for
        downstream logging (parity with HCPC's log format).
        """
        self._ensure_tree()
        q_emb = np.asarray(
            self.pipeline.embeddings.embed_query(query), dtype=np.float32
        )

        # Split budget: at least 1 slot for summaries if any exist, rest leaves.
        n_leaf_slots = int(np.ceil(self.top_k * self.mix_ratio))
        n_sum_slots = max(0, self.top_k - n_leaf_slots)
        if self._summaries and n_sum_slots == 0:
            # Force at least one summary so RAPTOR actually uses its tree.
            n_sum_slots = 1
            n_leaf_slots = max(0, self.top_k - n_sum_slots)

        leaf_idx, leaf_sim = self._topk(
            q_emb, self._leaf_embs if self._leaf_embs is not None
            else np.zeros((0, q_emb.shape[0])), n_leaf_slots)
        sum_idx, sum_sim = self._topk(
            q_emb, self._sum_embs if self._sum_embs is not None
            else np.zeros((0, q_emb.shape[0])), n_sum_slots)

        selected: List[Document] = []
        for rank, (i, s) in enumerate(zip(leaf_idx, leaf_sim)):
            d = self._leaves[int(i)]
            d.metadata = dict(d.metadata or {})
            d.metadata.update({"raptor_score": float(s), "raptor_rank": rank})
            selected.append(d)
        for rank, (i, s) in enumerate(zip(sum_idx, sum_sim)):
            d = self._summaries[int(i)]
            d.metadata = dict(d.metadata or {})
            d.metadata.update({"raptor_score": float(s), "raptor_rank": rank})
            selected.append(d)

        log = {
            "strategy": "raptor",
            "n_leaves_total":    len(self._leaves),
            "n_summaries_total": len(self._summaries),
            "n_leaves_returned":    int(len(leaf_idx)),
            "n_summaries_returned": int(len(sum_idx)),
            "leaf_sims": [round(float(s), 4) for s in leaf_sim],
            "sum_sims":  [round(float(s), 4) for s in sum_sim],
            # Parity with HCPC log: `refined` means "a summary was substituted"
            "refined": bool(len(sum_idx) > 0),
            # context_coherence slot kept so downstream code (_eval_one_query)
            # can pull it uniformly even though RAPTOR has no CCS concept.
            "context_coherence": -1.0,
        }
        return selected, log

    # Some callers treat retrievers as callable.
    def __call__(self, query: str):
        return self.retrieve(query)
