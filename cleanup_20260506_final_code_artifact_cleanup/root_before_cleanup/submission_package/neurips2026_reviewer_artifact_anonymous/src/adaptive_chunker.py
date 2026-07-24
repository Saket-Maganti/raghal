"""
Adaptive Chunking Strategies for RAG

Provides two alternatives to fixed RecursiveCharacterTextSplitter:

  SemanticChunker  — groups adjacent sentences by embedding cosine similarity;
                     starts a new chunk when semantic coherence drops below a
                     threshold or the character budget is exceeded.

  DynamicChunker   — respects paragraph structure; merges short paragraphs to
                     meet a minimum size and sub-splits long ones using
                     RecursiveCharacterTextSplitter.

Both expose the same interface as LangChain text splitters:
    chunker.split_documents(documents) → list[Document]

Usage:
    from src.adaptive_chunker import SemanticChunker, DynamicChunker, get_chunker

    # Semantic chunking (requires an initialized embeddings object)
    chunker = SemanticChunker(embeddings=pipeline.embeddings, similarity_threshold=0.5)

    # Dynamic / structure-aware chunking (no embeddings needed)
    chunker = DynamicChunker(min_chunk_chars=300, max_chunk_chars=3000)

    # Factory helper
    chunker = get_chunker("semantic", embeddings=emb)
    chunker = get_chunker("dynamic")
    chunker = get_chunker("fixed", chunk_size=512, chunk_overlap=50)
"""

from __future__ import annotations

import re
from typing import Any, Optional

import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ── Utilities ─────────────────────────────────────────────────────────────────

def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using punctuation-boundary regex."""
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if len(s.strip()) > 15]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two numpy vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ── Semantic Chunker ──────────────────────────────────────────────────────────

class SemanticChunker:
    """
    Groups adjacent sentences into chunks based on embedding cosine similarity.

    Algorithm:
      1. Split the document into sentences.
      2. Embed all sentences in a single batched call.
      3. Walk forward: append a sentence to the current chunk while
         (a) its embedding is similar enough to the running chunk centroid, and
         (b) the accumulated text stays under max_chunk_chars.
      4. Start a new chunk when either condition breaks.
      5. Never emit a chunk shorter than min_chunk_chars (merge forward instead).

    Parameters
    ----------
    embeddings : LangChain-compatible embeddings object (must support
                 .embed_documents(list[str]) and .embed_query(str)).
    similarity_threshold : float in [0, 1]. Sentences below this cosine
                           similarity to the current chunk centroid trigger
                           a new chunk. Higher = tighter semantic cohesion,
                           smaller chunks. Lower = looser, larger chunks.
    max_chunk_chars : hard cap on chunk character length (~4 chars/token).
    min_chunk_chars : minimum before a chunk is emitted.
    """

    STRATEGY = "semantic"

    def __init__(
        self,
        embeddings: Any,
        similarity_threshold: float = 0.5,
        max_chunk_chars: int = 3000,
        min_chunk_chars: int = 200,
    ):
        self.embeddings = embeddings
        self.threshold = similarity_threshold
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars

        # Fallback splitter if embedding call fails
        self._fallback = RecursiveCharacterTextSplitter(
            chunk_size=512, chunk_overlap=50
        )

    # ── Public interface ──────────────────────────────────────────────────────

    def split_documents(self, documents: list[Document]) -> list[Document]:
        """Chunk a list of LangChain Documents, preserving metadata."""
        result: list[Document] = []
        for doc in documents:
            chunks = self._chunk_text(doc.page_content)
            for idx, text in enumerate(chunks):
                result.append(Document(
                    page_content=text,
                    metadata={
                        **doc.metadata,
                        "chunk_index": idx,
                        "chunk_strategy": self.STRATEGY,
                        "similarity_threshold": self.threshold,
                    }
                ))
        return result

    # ── Internal ──────────────────────────────────────────────────────────────

    def _chunk_text(self, text: str) -> list[str]:
        sentences = _split_sentences(text)

        if len(sentences) <= 1:
            return [text] if text.strip() else []

        # Batch-embed all sentences
        try:
            raw_embs = self.embeddings.embed_documents(sentences)
            sent_embs = [np.array(e, dtype=np.float32) for e in raw_embs]
        except Exception as exc:
            print(f"[SemanticChunker] Embedding failed ({exc}); using fallback splitter.")
            return [d.page_content for d in self._fallback.create_documents([text])]

        chunks: list[str] = []
        cur_sentences: list[str] = [sentences[0]]
        cur_embs: list[np.ndarray] = [sent_embs[0]]

        for i in range(1, len(sentences)):
            centroid = np.mean(cur_embs, axis=0)
            sim = _cosine_similarity(centroid, sent_embs[i])
            projected_len = len(" ".join(cur_sentences)) + len(sentences[i])

            if sim >= self.threshold and projected_len < self.max_chunk_chars:
                cur_sentences.append(sentences[i])
                cur_embs.append(sent_embs[i])
            else:
                cur_text = " ".join(cur_sentences)
                if len(cur_text) >= self.min_chunk_chars:
                    chunks.append(cur_text)
                    cur_sentences = [sentences[i]]
                    cur_embs = [sent_embs[i]]
                else:
                    # Buffer too short: absorb regardless of similarity
                    cur_sentences.append(sentences[i])
                    cur_embs.append(sent_embs[i])

        if cur_sentences:
            chunks.append(" ".join(cur_sentences))

        return [c for c in chunks if c.strip()] or [text]


# ── Dynamic Chunker ───────────────────────────────────────────────────────────

class DynamicChunker:
    """
    Structure-aware chunker that respects natural paragraph boundaries.

    Algorithm:
      1. Split the document on double-newline paragraph boundaries.
      2. Walk forward accumulating paragraphs into a buffer.
      3. When the buffer reaches min_chunk_chars, emit it as a chunk.
      4. When a single paragraph exceeds max_chunk_chars, sub-split it with
         RecursiveCharacterTextSplitter before continuing.

    No embeddings are required. This is a fast, corpus-agnostic alternative
    that works well for structured documents (scientific abstracts, news, FAQs).

    Parameters
    ----------
    min_chunk_chars : minimum character length before emitting a chunk.
    max_chunk_chars : maximum character length; longer paragraphs are sub-split.
    overlap_chars   : overlap passed to the fallback splitter for sub-splitting.
    """

    STRATEGY = "dynamic"

    def __init__(
        self,
        min_chunk_chars: int = 300,
        max_chunk_chars: int = 3000,
        overlap_chars: int = 100,
    ):
        self.min_chunk_chars = min_chunk_chars
        self.max_chunk_chars = max_chunk_chars
        self._subsplitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_chars,
            chunk_overlap=overlap_chars,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    # ── Public interface ──────────────────────────────────────────────────────

    def split_documents(self, documents: list[Document]) -> list[Document]:
        """Chunk a list of LangChain Documents, preserving metadata."""
        result: list[Document] = []
        for doc in documents:
            chunks = self._chunk_text(doc.page_content)
            for idx, text in enumerate(chunks):
                result.append(Document(
                    page_content=text,
                    metadata={
                        **doc.metadata,
                        "chunk_index": idx,
                        "chunk_strategy": self.STRATEGY,
                        "min_chunk_chars": self.min_chunk_chars,
                        "max_chunk_chars": self.max_chunk_chars,
                    }
                ))
        return result

    # ── Internal ──────────────────────────────────────────────────────────────

    def _chunk_text(self, text: str) -> list[str]:
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

        if not paragraphs:
            return [text] if text.strip() else []

        output: list[str] = []
        buffer = ""

        for para in paragraphs:
            if len(para) > self.max_chunk_chars:
                # Flush current buffer first
                if buffer.strip():
                    output.append(buffer.strip())
                    buffer = ""
                # Sub-split the oversized paragraph
                sub_docs = self._subsplitter.create_documents([para])
                output.extend(d.page_content for d in sub_docs if d.page_content.strip())
            else:
                candidate = (buffer + "\n\n" + para).strip() if buffer else para
                if len(candidate) >= self.min_chunk_chars:
                    output.append(candidate)
                    buffer = ""
                else:
                    buffer = candidate

        if buffer.strip():
            output.append(buffer.strip())

        return [c for c in output if c] or [text]


# ── Factory ───────────────────────────────────────────────────────────────────

def get_chunker(
    strategy: str,
    embeddings: Optional[Any] = None,
    **kwargs: Any,
) -> Any:
    """
    Return a chunker for the given strategy.

    Parameters
    ----------
    strategy   : "fixed" | "semantic" | "dynamic"
    embeddings : required only for strategy="semantic"
    **kwargs   : forwarded to the selected chunker constructor

    Returns a chunker with a .split_documents(list[Document]) method.
    """
    if strategy == "fixed":
        chunk_size = kwargs.get("chunk_size", 512)
        chunk_overlap = kwargs.get("chunk_overlap", int(chunk_size * 0.1))
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    elif strategy == "semantic":
        if embeddings is None:
            raise ValueError("SemanticChunker requires an embeddings object (pass embeddings=...).")
        return SemanticChunker(embeddings=embeddings, **kwargs)
    elif strategy == "dynamic":
        return DynamicChunker(**kwargs)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy!r}. Choose from: fixed, semantic, dynamic.")
