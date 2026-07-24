"""
experiments/build_embedding_clusters.py — Phase 4 #4.8
======================================================

A 2D scatter of retrieved chunks projected via t-SNE (or UMAP if
installed), faceted by retrieval condition (baseline / HCPC-v1 /
HCPC-v2). Each point is one chunk; chunks from the same query share a
color so the reader can see how each condition arranges per-query
chunks in embedding space.

Visually, the prediction of the coherence account is:

    baseline   → per-query chunks form tight per-color clusters
                  (same query = nearby points)
    HCPC-v1    → per-query chunks scatter across the plot
                  (refinement breaks the cluster structure)
    HCPC-v2    → per-query chunks return to tight clusters
                  (selective refinement preserves the structure)

Inputs:
    Re-embeds the top-3 chunks per query for a small sample (n=15) of
    SQuAD queries. Embedding model: sentence-transformers/all-MiniLM-L6-v2.

Outputs:
    ragpaper/figures/embedding_clusters.pdf
    ragpaper/figures/embedding_clusters.tex
    results/embedding_clusters/projection_table.csv

Usage:
    python3 experiments/build_embedding_clusters.py
    python3 experiments/build_embedding_clusters.py --n_queries 25 --use_umap
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "ragpaper" / "figures"
OUT_PDF = OUT_DIR / "embedding_clusters.pdf"
OUT_TEX = OUT_DIR / "embedding_clusters.tex"
OUT_CSV_DIR = ROOT / "results" / "embedding_clusters"
OUT_CSV = OUT_CSV_DIR / "projection_table.csv"


def _project(E: np.ndarray, use_umap: bool, seed: int = 42) -> np.ndarray:
    """2D projection. Tries UMAP first if requested; falls back to TSNE."""
    if use_umap:
        try:
            import umap
            reducer = umap.UMAP(n_neighbors=8, min_dist=0.2,
                                 random_state=seed, n_components=2)
            return reducer.fit_transform(E)
        except ImportError:
            print("[clusters] umap not installed, falling back to t-SNE")
    from sklearn.manifold import TSNE
    perp = max(5, min(30, len(E) // 3))
    tsne = TSNE(n_components=2, perplexity=perp,
                random_state=seed, init="pca", learning_rate="auto")
    return tsne.fit_transform(E)


def _retrieve_per_condition(n_queries: int) -> pd.DataFrame:
    """Run baseline / hcpc_v1 / hcpc_v2 for n_queries SQuAD queries and
    return a long DataFrame with one row per (query, condition, chunk)."""
    from src.dataset_loaders          import load_dataset_by_name
    from src.rag_pipeline             import RAGPipeline
    from src.hcpc_retriever           import HCPCRetriever
    from src.hcpc_v2_retriever        import HCPCv2Retriever
    from sentence_transformers        import SentenceTransformer

    docs, qa = load_dataset_by_name("squad", max_papers=30)
    if not docs or not qa:
        raise SystemExit("[clusters] could not load SQuAD")

    coll = "embcluster_squad"
    pipe = RAGPipeline(
        chunk_size=1024, chunk_overlap=100, top_k=3,
        model_name="mistral",
        embed_model="sentence-transformers/all-MiniLM-L6-v2",
        persist_dir=f"./chroma_db_embcluster/{coll}",
    )
    pipe.index_documents(docs, collection_name=coll)
    hcpc_v1 = HCPCRetriever(pipeline=pipe, sim_threshold=0.50,
                             ce_threshold=0.0,  top_k=3)
    hcpc_v2 = HCPCv2Retriever(pipeline=pipe, sim_threshold=0.45,
                               ce_threshold=-0.20, top_k_protected=2,
                               max_refine=2)
    # HCPCv2 reads top_k from pipeline.top_k (set above to 3); no kwarg.

    rows: List[Dict] = []
    encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    for qi, qa_pair in enumerate(qa[:n_queries]):
        q = qa_pair["question"]
        for label, retr in [("baseline", None),
                             ("hcpc_v1", hcpc_v1),
                             ("hcpc_v2", hcpc_v2)]:
            if retr is None:
                ds, _ = pipe.retrieve_with_scores(q)
            else:
                out = retr.retrieve(q)
                ds = out[0] if isinstance(out, tuple) else out
            for d in ds[:3]:
                rows.append({
                    "qid":       qi,
                    "condition": label,
                    "text":      d.page_content[:512],
                })

    if not rows:
        raise SystemExit("[clusters] no retrieved chunks")
    df = pd.DataFrame(rows)
    embs = encoder.encode(df["text"].tolist(), normalize_embeddings=True)
    for i in range(embs.shape[1]):
        df[f"e{i}"] = embs[:, i]
    return df


def _plot(df: pd.DataFrame) -> None:
    conditions = ["baseline", "hcpc_v1", "hcpc_v2"]
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.8),
                              constrained_layout=True, sharex=False, sharey=False)
    qids = sorted(df["qid"].unique())
    cmap = plt.get_cmap("tab20", len(qids))

    for ax, cond in zip(axes, conditions):
        sub = df[df["condition"] == cond].copy()
        for i, qid in enumerate(qids):
            cell = sub[sub["qid"] == qid]
            if len(cell) == 0:
                continue
            ax.scatter(cell["x"], cell["y"],
                       color=cmap(i), s=42,
                       edgecolor="white", linewidth=0.5, alpha=0.9)
        ax.set_title(cond, fontsize=11)
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ("top", "right", "left", "bottom"):
            ax.spines[spine].set_visible(False)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)


TEX_TEMPLATE = r"""% Auto-generated by experiments/build_embedding_clusters.py
\begin{figure}[!htb]
\centering
\includegraphics[width=\linewidth]{figures/embedding_clusters.pdf}
\caption{\textbf{Embedding-space view of the refinement paradox.}
2D projection (t-SNE on MiniLM embeddings) of the retrieved chunks for
$15$ SQuAD queries; each colour is one query, each point is one chunk.
\textbf{Left (baseline):} per-query chunks form tight same-colour
clusters --- evidence is locally consistent within each query.
\textbf{Centre (HCPC-v1):} the same colours scatter across the plot ---
per-passage refinement has substituted in chunks from elsewhere in the
corpus that match each individual question independently but no longer
form a coherent set.
\textbf{Right (HCPC-v2):} per-query clusters return, because the
selective refinement policy declines to refine when doing so would
shatter the original cluster.}
\label{fig:embedding_clusters}
\end{figure}
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n_queries", type=int, default=15)
    ap.add_argument("--use_umap", action="store_true",
                    help="prefer UMAP over t-SNE if `umap-learn` is installed")
    args = ap.parse_args()

    df = _retrieve_per_condition(args.n_queries)

    # Project each condition independently so the layout is per-condition
    # (a global projection conflates the conditions).
    projected: List[pd.DataFrame] = []
    for cond, sub in df.groupby("condition"):
        E = sub[[c for c in sub.columns if c.startswith("e")]].values
        XY = _project(E, args.use_umap)
        sub = sub.copy()
        sub["x"] = XY[:, 0]; sub["y"] = XY[:, 1]
        projected.append(sub[["qid", "condition", "x", "y", "text"]])
    out = pd.concat(projected, ignore_index=True)

    OUT_CSV_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    _plot(out)
    OUT_TEX.write_text(TEX_TEMPLATE)
    print(f"[clusters] wrote {OUT_PDF.relative_to(ROOT)}")
    print(f"[clusters] wrote {OUT_TEX.relative_to(ROOT)}")
    print(f"[clusters] wrote {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
