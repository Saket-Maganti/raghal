"""
space/app.py — Phase 2 Item 10 (HF Space demo)
==============================================

A Gradio demo for the paper "The Coherence Paradox in RAG".  Designed to run
on a free HF Space (CPU-basic / 16 GB RAM) without requiring Ollama or any
LLM in the loop — all the interactive widgets depend only on a sentence
embedder that already fits in CPU memory.

The demo has three tabs:

1. **CCS calculator** — paste 2–10 passages, get the Context Coherence Score
   defined in our paper (mean pairwise cosine − std).  Lets a visitor build
   intuition for what "coherent context" means.

2. **Paradox explorer** — static browser over pre-computed results CSVs
   (`results/multidataset/coherence_paradox.csv`, `results/headtohead/
   summary.csv`, `results/deployment_figure/pareto_summary.csv`).  No
   compute, just a nicely filtered pandas table + the deployment figure.

3. **About** — one-pager describing the paradox, the HCPC-v1/v2 remedy,
   and the benchmark release (`release/context_coherence_bench_v1/`).

Launch locally:
    pip install gradio sentence-transformers pandas numpy
    python space/app.py

Deploy to HF:
    Copy `space/app.py`, `requirements.txt`, and a slim `results/` subset
    (the three CSVs above + the PNG) into a new HF Space repo.
"""

from __future__ import annotations

import os
import sys
from typing import List, Tuple

import numpy as np
import pandas as pd
import gradio as gr

# Make imports resolve whether launched from repo root or space/ directly.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ─────────────────────────────────────────────────────────────────────────────
# CCS — reused from the paper's own implementation so numbers match
# ─────────────────────────────────────────────────────────────────────────────

_EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_embedder = None   # lazy


def _get_embedder():
    global _embedder
    if _embedder is None:
        # Import lazy so `gradio --help` doesn't pay for the 90 MB model.
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(_EMBED_MODEL_NAME)
    return _embedder


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def ccs_of(passages: List[str]) -> Tuple[float, float, float, List[List[float]]]:
    """Return (CCS, mean_sim, std_sim, pairwise_matrix).

    Mirrors `HCPCv2Retriever._compute_ccs` exactly so demo numbers match
    what's reported in the paper.
    """
    passages = [p.strip() for p in passages if p and p.strip()]
    if len(passages) < 2:
        return 0.0, 0.0, 0.0, [[1.0]] if passages else [[]]
    embs = np.asarray(_get_embedder().encode(passages), dtype=np.float32)
    n = len(embs)
    mat = [[round(_cosine(embs[i], embs[j]), 4) for j in range(n)]
           for i in range(n)]
    pair = [mat[i][j] for i in range(n) for j in range(i + 1, n)]
    mean_s = float(np.mean(pair))
    std_s  = float(np.std(pair))
    return round(mean_s - std_s, 4), round(mean_s, 4), round(std_s, 4), mat


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1 — CCS calculator
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_PASSAGES = (
    "The Denver Broncos won Super Bowl 50.\n"
    "---\n"
    "Super Bowl 50 was held at Levi's Stadium in the San Francisco Bay Area.\n"
    "---\n"
    "Peyton Manning was named Super Bowl 50 MVP."
)


def ccs_ui(raw: str):
    parts = [p for p in raw.split("---") if p.strip()]
    if len(parts) < 2:
        return 0.0, 0.0, 0.0, pd.DataFrame({"msg": ["Need ≥ 2 passages separated by `---`."]})
    ccs, mean_s, std_s, mat = ccs_of(parts)
    df = pd.DataFrame(
        mat,
        index=[f"P{i+1}" for i in range(len(mat))],
        columns=[f"P{i+1}" for i in range(len(mat))],
    )
    return ccs, mean_s, std_s, df


# ─────────────────────────────────────────────────────────────────────────────
# Tab 2 — Paradox explorer (static CSV browser)
# ─────────────────────────────────────────────────────────────────────────────

def _safe_read(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame({"note": [f"missing: {path}"]})
    try:
        return pd.read_csv(path)
    except Exception as exc:
        return pd.DataFrame({"error": [str(exc)]})


PARADOX_PATH = os.path.join(ROOT, "results", "multidataset", "coherence_paradox.csv")
HTH_PATH     = os.path.join(ROOT, "results", "headtohead",  "summary.csv")
PARETO_PATH  = os.path.join(ROOT, "results", "deployment_figure", "pareto_summary.csv")
FIG_PATH     = os.path.join(ROOT, "results", "deployment_figure", "latency_vs_faith.png")


def filter_paradox(ds_filter: str):
    df = _safe_read(PARADOX_PATH)
    if "dataset" in df.columns and ds_filter and ds_filter != "all":
        df = df[df["dataset"] == ds_filter].reset_index(drop=True)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Tab 3 — About
# ─────────────────────────────────────────────────────────────────────────────

ABOUT_MD = """
# The Coherence Paradox in RAG

**Short version.** Better per-passage retrieval can *hurt* answer
faithfulness, because aggressive pruning fragments the surrounding context
the generator needs to stay grounded.  We call this the **coherence
paradox**: `faith_baseline − faith_hcpc_v1 > 0` across 6 datasets × 3
generators when retrieval uses an undersized embedder or a hard domain.

**Why it matters.** It is not a prompt bug, not a temperature bug, and not
a benchmark artifact — we rule all three out with dedicated ablations
(see `results/noise_injection/`, `results/prompt_ablation/`,
`results/rag_vs_zeroshot/`).  It is a property of the
**retrieval–generation alignment** itself.

**Our remedy: HCPC-v2.** A simple two-signal gate (sim + cross-encoder)
with a "protected top-k" so the generator always has a broad window, then
*bounded* sub-chunk refinement only on weak passages.  Ships with a
generator-free coherence diagnostic (CCS = mean pairwise similarity − std)
that predicts hallucination at retrieval time.

**Benchmark.** We release `context_coherence_bench_v1/` (HF-loadable):
200 adversarial cases across four coherence-stress categories, plus the
CCS + faith-drop scoring scripts so any future retriever can post a
paradox number in one command.

**Paper.** See `ragpaper/` in the repo (LaTeX source + compiled PDF).
"""


# ─────────────────────────────────────────────────────────────────────────────
# Build the Gradio app
# ─────────────────────────────────────────────────────────────────────────────

def build_app() -> gr.Blocks:
    with gr.Blocks(title="Coherence Paradox — NeurIPS 2026 demo") as app:
        gr.Markdown("# 🧭 Coherence Paradox in RAG — interactive demo\n"
                    "Paper appendix companion — all widgets run CPU-only.")

        with gr.Tab("CCS calculator"):
            gr.Markdown(
                "Paste 2–10 passages separated by `---` on their own line. "
                "We report CCS = mean pairwise cosine − std of pairwise cosines, "
                "computed with the same `all-MiniLM-L6-v2` embedder used in "
                "the paper. Higher = more coherent context."
            )
            inp = gr.Textbox(lines=12, value=DEFAULT_PASSAGES,
                             label="Passages (separated by `---`)")
            with gr.Row():
                ccs_n = gr.Number(label="CCS", precision=4)
                mean_n = gr.Number(label="mean pairwise sim", precision=4)
                std_n = gr.Number(label="std pairwise sim", precision=4)
            mat_df = gr.Dataframe(label="Pairwise cosine matrix",
                                  interactive=False, wrap=True)
            btn = gr.Button("Compute CCS", variant="primary")
            btn.click(ccs_ui, inputs=inp, outputs=[ccs_n, mean_n, std_n, mat_df])

        with gr.Tab("Paradox explorer"):
            gr.Markdown("### Per-(dataset, model) coherence paradox")
            gr.Markdown("`paradox_drop` = faith_baseline − faith_hcpc_v1. "
                        "Positive = paradox confirmed.  "
                        "`v2_recovery` = faith_v2 − faith_v1.")
            ds_choices = ["all", "squad", "pubmedqa", "naturalqs",
                          "triviaqa", "hotpotqa", "financebench"]
            ds_dd = gr.Dropdown(ds_choices, value="all", label="Filter dataset")
            paradox_df = gr.Dataframe(value=_safe_read(PARADOX_PATH),
                                      interactive=False, wrap=True)
            ds_dd.change(filter_paradox, inputs=ds_dd, outputs=paradox_df)

            gr.Markdown("---\n### Head-to-head retrievers")
            gr.Dataframe(value=_safe_read(HTH_PATH), interactive=False, wrap=True)

            gr.Markdown("---\n### Deployment Pareto frontier "
                        "(latency vs faithfulness)")
            gr.Dataframe(value=_safe_read(PARETO_PATH),
                         interactive=False, wrap=True)
            if os.path.exists(FIG_PATH):
                gr.Image(value=FIG_PATH, label="Deployment figure",
                         interactive=False)

        with gr.Tab("About"):
            gr.Markdown(ABOUT_MD)

    return app


if __name__ == "__main__":
    build_app().launch(server_name="0.0.0.0")
