"""
RAG Pipeline with Hallucination Detection
Uses Ollama (Mistral-7B) + ChromaDB + LangChain

Changelog
---------
- Added optional `chunker` parameter to __init__ and index_documents.
  When supplied, the custom chunker (e.g. SemanticChunker / DynamicChunker)
  replaces the default RecursiveCharacterTextSplitter. Existing behavior is
  fully preserved when chunker=None (the default).
- Added retrieve_with_scores() which returns (docs, similarity_scores) for
  retrieval quality metric logging.
"""

import os
import time
from typing import Any, Optional

from langchain_ollama import OllamaLLM
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate


def _best_device() -> str:
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


# ── Prompt templates ──────────────────────────────────────────────────────────

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a helpful assistant that answers questions based ONLY on the provided context.
If the answer is not in the context, say "I cannot find this information in the provided context."

Context:
{context}

Question: {question}

Answer based strictly on the context above:"""
)


# ── RAG Pipeline ──────────────────────────────────────────────────────────────

class RAGPipeline:
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        top_k: int = 3,
        model_name: str = "mistral",
        embed_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        persist_dir: str = "./chroma_db",
        chunker: Optional[Any] = None,          # NEW: inject adaptive chunker
        embeddings: Optional[Any] = None,       # NEW: inject custom embedder
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.model_name = model_name
        self.persist_dir = persist_dir

        if embeddings is not None:
            # Caller supplied a fully-built embedder (e.g. PrefixedSTEmbeddings
            # for BGE/E5/GTE in the multi-retriever ablation). Use it as-is.
            print(f"[RAG] Using injected embeddings: {type(embeddings).__name__}")
            self.embeddings = embeddings
        else:
            print(f"[RAG] Loading embedding model: {embed_model}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embed_model,
                model_kwargs={"device": _best_device()}
            )

        print(f"[RAG] Connecting to Ollama ({model_name})")
        self.llm = OllamaLLM(model=model_name, temperature=0.1)

        # Default fixed-size splitter (used when chunker=None)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        # Optional custom chunker (SemanticChunker / DynamicChunker)
        self.chunker = chunker

        self.vectorstore: Optional[Chroma] = None

    # ── Indexing ──────────────────────────────────────────────────────────────

    def index_documents(
        self,
        documents: list[Document],
        collection_name: str = "qasper",
        chunker: Optional[Any] = None,  # override instance chunker for this call
    ):
        """Chunk and embed documents into ChromaDB.

        Chunking priority: argument > self.chunker > default text_splitter.
        """
        active_chunker = chunker or self.chunker
        print(f"[RAG] Splitting {len(documents)} documents into chunks...")
        if active_chunker is not None:
            strategy = getattr(active_chunker, "STRATEGY", "custom")
            print(f"[RAG] Using adaptive chunker: {strategy}")
            chunks = active_chunker.split_documents(documents)
        else:
            chunks = self.text_splitter.split_documents(documents)
        print(f"[RAG] Created {len(chunks)} chunks")

        print("[RAG] Building vector store...")
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name=collection_name,
            persist_directory=self.persist_dir
        )
        print(f"[RAG] Indexed {len(chunks)} chunks into ChromaDB")
        return len(chunks)

    def load_existing_index(self, collection_name: str = "qasper"):
        """Load an existing ChromaDB index from disk."""
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_dir
        )
        print(f"[RAG] Loaded existing index from {self.persist_dir}")

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def retrieve(self, query: str) -> list[Document]:
        """Retrieve top-k relevant chunks for a query."""
        if self.vectorstore is None:
            raise RuntimeError("Vector store not initialized. Call index_documents() first.")
        return self.vectorstore.similarity_search(query, k=self.top_k)

    def retrieve_with_scores(self, query: str) -> tuple[list[Document], list[float]]:
        """Retrieve top-k chunks and their cosine similarity scores.

        Returns
        -------
        (docs, scores) where scores[i] is the cosine similarity for docs[i].
        Scores are in [0, 1] (Chroma returns distance; we convert to similarity).
        """
        if self.vectorstore is None:
            raise RuntimeError("Vector store not initialized. Call index_documents() first.")
        results = self.vectorstore.similarity_search_with_score(query, k=self.top_k)
        docs = [doc for doc, _ in results]
        # Chroma returns L2 distance; convert to cosine similarity proxy [0,1]
        scores = [round(max(0.0, 1.0 - float(score)), 4) for _, score in results]
        return docs, scores

    # ── Generation ────────────────────────────────────────────────────────────

    def generate(self, question: str, retrieved_docs: list[Document]) -> dict:
        """Generate an answer from retrieved context."""
        context = "\n\n---\n\n".join([doc.page_content for doc in retrieved_docs])
        prompt = RAG_PROMPT.format(context=context, question=question)

        t0 = time.time()
        answer = self.llm.invoke(prompt)
        latency = round(time.time() - t0, 2)

        return {
            "question": question,
            "answer": answer,
            "context": context,
            "retrieved_docs": retrieved_docs,
            "latency_s": latency
        }

    # ── Full Pipeline ─────────────────────────────────────────────────────────

    def query(self, question: str) -> dict:
        """End-to-end: retrieve → generate."""
        retrieved = self.retrieve(question)
        result = self.generate(question, retrieved)
        return result
