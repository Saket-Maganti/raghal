"""
src/embedders.py
Registry of dense retrievers used in the multi-retriever ablation
(Item #8, added after the Apr-2026 review by Prof. <reviewer>).

Why this exists
---------------
Every prior phase used a single embedder, ``sentence-transformers/all-MiniLM-L6-v2``
(82 M parameters, 2019 vintage). A reviewer can fairly object that the
"refinement paradox" we report is an artefact of a *weak* retriever, and
that a stronger embedder would close the gap. To distinguish "coherence
is causal" from "weak embedding causes the artefact", we rerun the central
Phase-6 contrast (baseline / HCPC-v1 / HCPC-v2) across four embedders that
span the modern strong-retriever frontier:

    MiniLM-L6   — 82 M, weak baseline (existing experiments)
    BGE-large   — 335 M, MTEB top-tier symmetric retriever
    E5-large-v2 — 335 M, contrastive asymmetric retriever
    GTE-large   — 335 M, alternative training family

If the paradox persists across all four, coherence is the causal mediator.
If it vanishes with the strong retrievers, the framing must change to
"failure mode of weak retrievers" (still publishable, but honest).

Asymmetric models (E5, BGE) require *prefix-conditioned* embeddings
("query: " vs "passage: ") to match their training. We expose a thin
LangChain-compatible wrapper that applies the right prefix per call site,
so the rest of the pipeline (RAGPipeline, Chroma, ChromaDB) is untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class EmbedderSpec:
    """Static metadata + prefix conventions for one retriever."""
    short_name:        str    # registry key
    hf_name:           str    # HuggingFace identifier
    display_name:      str    # for tables/figures
    parameters:        int
    embed_dim:         int
    family:            str
    query_prefix:      str = ""
    passage_prefix:    str = ""
    normalize:         bool  = True
    notes:             str   = ""


EMBEDDERS: Dict[str, EmbedderSpec] = {
    "minilm": EmbedderSpec(
        short_name    = "minilm",
        hf_name       = "sentence-transformers/all-MiniLM-L6-v2",
        display_name  = "MiniLM-L6 (82M, baseline)",
        parameters    = 22_000_000,   # 22M params; 384-dim
        embed_dim     = 384,
        family        = "sentence-transformers",
        query_prefix  = "",
        passage_prefix= "",
        normalize     = True,
        notes         = "Original baseline used in all prior phases.",
    ),
    "bge-large": EmbedderSpec(
        short_name    = "bge-large",
        hf_name       = "BAAI/bge-large-en-v1.5",
        display_name  = "BGE-large-en-v1.5 (335M)",
        parameters    = 335_000_000,
        embed_dim     = 1024,
        family        = "bge",
        query_prefix  = "Represent this sentence for searching relevant passages: ",
        passage_prefix= "",
        normalize     = True,
        notes         = "Asymmetric: query gets a representation prompt; passages do not.",
    ),
    "e5-large": EmbedderSpec(
        short_name    = "e5-large",
        hf_name       = "intfloat/e5-large-v2",
        display_name  = "E5-large-v2 (335M)",
        parameters    = 335_000_000,
        embed_dim     = 1024,
        family        = "e5",
        query_prefix  = "query: ",
        passage_prefix= "passage: ",
        normalize     = True,
        notes         = "Contrastive asymmetric; both sides need their own prefix.",
    ),
    "gte-large": EmbedderSpec(
        short_name    = "gte-large",
        hf_name       = "thenlper/gte-large",
        display_name  = "GTE-large (335M)",
        parameters    = 335_000_000,
        embed_dim     = 1024,
        family        = "gte",
        query_prefix  = "",
        passage_prefix= "",
        normalize     = True,
        notes         = "Symmetric; trained on diverse retrieval mixtures.",
    ),
}


# ── LangChain-compatible wrapper ─────────────────────────────────────────────

class PrefixedSTEmbeddings:
    """Sentence-Transformers embedder with prefix-conditioned encoding.

    Implements the two-method LangChain protocol that ChromaDB depends on:
      - ``embed_query(text: str) -> List[float]``
      - ``embed_documents(texts: List[str]) -> List[List[float]]``

    The prefix policy is read from the ``EmbedderSpec`` so callers do not
    have to remember which model needs which prefix. Models are loaded
    lazily on the first call so the registry can be imported cheaply.
    """

    def __init__(
        self,
        spec: EmbedderSpec,
        device: Optional[str] = None,
        batch_size: int = 32,
    ):
        self.spec = spec
        self._device = device or self._auto_device()
        self.batch_size = batch_size
        self._model = None

    @staticmethod
    def _auto_device() -> str:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                return "mps"
        except Exception:
            pass
        return "cpu"

    def _lazy_load(self):
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer
        print(f"[Embed] Loading {self.spec.display_name} on {self._device}")
        self._model = SentenceTransformer(self.spec.hf_name, device=self._device)

    def embed_query(self, text: str) -> List[float]:
        self._lazy_load()
        prefixed = self.spec.query_prefix + text if self.spec.query_prefix else text
        vec = self._model.encode(
            [prefixed],
            normalize_embeddings=self.spec.normalize,
            show_progress_bar=False,
            convert_to_numpy=True,
        )[0]
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self._lazy_load()
        if self.spec.passage_prefix:
            prefixed = [self.spec.passage_prefix + t for t in texts]
        else:
            prefixed = list(texts)
        vecs = self._model.encode(
            prefixed,
            batch_size=self.batch_size,
            normalize_embeddings=self.spec.normalize,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return [v.tolist() for v in vecs]

    # Optional: matches the LangChain Embeddings ABC ``__call__``.
    def __call__(self, texts):
        if isinstance(texts, str):
            return self.embed_query(texts)
        return self.embed_documents(list(texts))


def build_embedder(short_name: str, device: Optional[str] = None) -> PrefixedSTEmbeddings:
    if short_name not in EMBEDDERS:
        raise ValueError(
            f"Unknown embedder {short_name!r}; choices = {list(EMBEDDERS)}"
        )
    return PrefixedSTEmbeddings(EMBEDDERS[short_name], device=device)


def list_embedders() -> List[str]:
    return list(EMBEDDERS.keys())


def display_table_md() -> str:
    lines = [
        "| Short name | Model | Params | Dim | Query prefix | Family |",
        "|------------|-------|--------|-----|--------------|--------|",
    ]
    for spec in EMBEDDERS.values():
        qp = spec.query_prefix.replace("|", "\\|") or "(none)"
        lines.append(
            f"| `{spec.short_name}` | {spec.hf_name} | "
            f"{spec.parameters/1e6:.0f}M | {spec.embed_dim} | "
            f"`{qp}` | {spec.family} |"
        )
    return "\n".join(lines)
