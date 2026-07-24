"""
experiments/run_mmr_baseline.py — Phase 7 #2a (MMR head-to-head)
================================================================

Compare HCPC-v$2$ against MMR (Maximal Marginal Relevance) — the
standard diversification baseline. Both try to balance per-passage
relevance and set-level structure; they make different trade-offs.

Conditions (5 per query):
    baseline    raw top-k retrieval, no diversification, no refinement
    hcpc_v1     refine all (paradox-prone)
    hcpc_v2     coherence-gated refinement (ours)
    mmr_05      MMR with λ=0.5 (balanced relevance/diversity)
    mmr_07      MMR with λ=0.7 (more relevance-weighted)

Outputs:
    results/mmr_baseline/per_query.csv
    results/mmr_baseline/summary.csv
    results/mmr_baseline/headtohead.csv     (paradox vs MMR-baseline-recovery)
    results/mmr_baseline/summary.md

Run (Ollama, ~2 hr, ~30 q × 2 datasets × 5 conditions = 300 calls):
    ollama serve &
    python3 experiments/run_mmr_baseline.py --datasets squad pubmedqa --n 30

Run (Groq, ~10 min, Kaggle-friendly):
    export GROQ_API_KEY=...
    python3 experiments/run_mmr_baseline.py --backend groq \\
        --model llama-3.3-70b --datasets squad pubmedqa --n 30
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

# Monkey-patch OllamaLLM so groq-backend runs don't hang on Kaggle.
if "--backend" in sys.argv and "groq" in sys.argv:
    import langchain_ollama
    class _StubOllama:
        def __init__(self, *args, **kwargs): pass
        def invoke(self, *args, **kwargs):
            raise RuntimeError("Stub OllamaLLM called — backend should be groq")
    langchain_ollama.OllamaLLM = _StubOllama

from src.dataset_loaders        import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline           import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever         import HCPCRetriever
from src.hcpc_v2_retriever      import HCPCv2Retriever
from src.mmr_retriever          import MMRRetriever
from src.retrieval_metrics      import compute_retrieval_quality

OUT_DIR = "results/mmr_baseline"
EMBED   = "sentence-transformers/all-MiniLM-L6-v2"
V1_SIM, V1_CE = 0.50,  0.00
V2_SIM, V2_CE = 0.45, -0.20


def _eval(pipe, qa, retriever, label, det):
    if retriever is None:
        docs, _ = pipe.retrieve_with_scores(qa["question"]); hlog = {}
    else:
        out = retriever.retrieve(qa["question"])
        docs, hlog = out if isinstance(out, tuple) else (out, {})
    g = pipe.generate(qa["question"], docs)
    n = det.detect(g["answer"], g["context"])
    rm = compute_retrieval_quality(qa["question"], docs, pipe.embeddings)
    return {
        "question":            qa["question"],
        "ground_truth":        qa.get("ground_truth", ""),
        "answer":              g["answer"],
        "condition":           label,
        "faithfulness_score":  n["faithfulness_score"],
        "is_hallucination":    n["is_hallucination"],
        "mean_retrieval_similarity": rm.get("mean_similarity", 0.0),
        "ccs":                 hlog.get("context_coherence", -1.0)
                                if isinstance(hlog, dict) else -1.0,
        "refined":             bool(hlog.get("refined", False))
                                if isinstance(hlog, dict) else False,
    }


def _make_llm(backend, model):
    if backend == "groq":
        from src.groq_llm import GroqLLM
        return GroqLLM(model=model, temperature=0.1)
    return None  # Ollama default in pipeline


def run(ds, n_q, backend, model, det):
    print(f"\n[MMR] {ds.upper()} × {backend}/{model}")
    docs, qa = load_dataset_by_name(ds, max_papers=30)
    if not docs or not qa: return []

    coll = f"mmr_{ds}_{model.replace('/', '_').replace('-', '_').replace('.', '_')}"
    pipe = RAGPipeline(
        chunk_size=1024, chunk_overlap=100, top_k=3,
        model_name=model, embed_model=EMBED,
        persist_dir=f"./chroma_db_mmr/{coll}",
    )
    pipe.index_documents(docs, collection_name=coll)
    if backend == "groq":
        from src.groq_llm import GroqLLM
        pipe.llm = GroqLLM(model=model, temperature=0.1)

    retrievers = [
        ("baseline", None),
        ("hcpc_v1",  HCPCRetriever(pipeline=pipe, sim_threshold=V1_SIM,
                                    ce_threshold=V1_CE, top_k=3)),
        ("hcpc_v2",  HCPCv2Retriever(pipeline=pipe, sim_threshold=V2_SIM,
                                      ce_threshold=V2_CE,
                                      top_k_protected=2, max_refine=2)),
        ("mmr_05",   MMRRetriever(pipeline=pipe, lambda_=0.5, top_k=3)),
        ("mmr_07",   MMRRetriever(pipeline=pipe, lambda_=0.7, top_k=3)),
    ]

    rows = []
    for qa_pair in qa[:n_q]:
        for label, retr in retrievers:
            try:
                r = _eval(pipe, qa_pair, retr, label, det)
                r["dataset"] = ds; r["model"] = model
                rows.append(r)
            except Exception as exc:
                print(f"[MMR] err {ds}/{label}: {exc}")
    return rows


def aggregate(rows):
    df = pd.DataFrame(rows)
    if df.empty: return df
    g = df.groupby(["dataset", "condition"])
    s = g.agg(
        n=("question", "count"),
        faith=("faithfulness_score", "mean"),
        halluc=("is_hallucination", "mean"),
        sim=("mean_retrieval_similarity", "mean"),
        ccs=("ccs", lambda x: float(x[x>=0].mean()) if (x>=0).any() else float("nan")),
        refine_rate=("refined", "mean"),
    ).reset_index()
    for c in ("faith", "halluc", "sim", "ccs", "refine_rate"):
        s[c] = s[c].round(4)
    return s


def headtohead(s):
    """Compare HCPC-v2 vs MMR, both vs baseline."""
    rows = []
    for ds, sub in s.groupby("dataset"):
        try:
            base = float(sub[sub["condition"] == "baseline"]["faith"].iloc[0])
            v1   = float(sub[sub["condition"] == "hcpc_v1"]["faith"].iloc[0])
            v2   = float(sub[sub["condition"] == "hcpc_v2"]["faith"].iloc[0])
            mmr5 = float(sub[sub["condition"] == "mmr_05"]["faith"].iloc[0])
            mmr7 = float(sub[sub["condition"] == "mmr_07"]["faith"].iloc[0])
        except IndexError: continue
        rows.append({
            "dataset":      ds,
            "faith_base":   base,
            "faith_v1":     v1,
            "faith_v2":     v2,
            "faith_mmr05":  mmr5,
            "faith_mmr07":  mmr7,
            "paradox":      round(base - v1, 4),
            "v2_recovery":  round(v2 - v1, 4),
            "mmr05_vs_base": round(mmr5 - base, 4),
            "mmr07_vs_base": round(mmr7 - base, 4),
            "v2_vs_mmr05":   round(v2 - mmr5, 4),   # >0 = v2 wins
            "v2_vs_mmr07":   round(v2 - mmr7, 4),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa"])
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--backend", choices=["ollama", "groq"], default="ollama")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()
    if args.model is None:
        args.model = "mistral" if args.backend == "ollama" else "llama-3.3-70b"

    os.makedirs(OUT_DIR, exist_ok=True)
    det = HallucinationDetector()

    all_rows = []
    for ds in args.datasets:
        if ds not in DATASET_REGISTRY:
            print(f"[MMR] unknown {ds}"); continue
        all_rows.extend(run(ds, args.n, args.backend, args.model, det))

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUT_DIR, "per_query.csv"), index=False)
    s = aggregate(all_rows); s.to_csv(os.path.join(OUT_DIR, "summary.csv"), index=False)
    h = headtohead(s); h.to_csv(os.path.join(OUT_DIR, "headtohead.csv"), index=False)

    md = ["# MMR baseline head-to-head (Phase 7 #2a)", "",
          "## Aggregated metrics", "", s.to_markdown(index=False), "",
          "## HCPC-v2 vs MMR head-to-head", "",
          h.to_markdown(index=False) if not h.empty else "(no data)", "",
          "Reading: `v2_vs_mmr05 > 0` means HCPC-v2 beats MMR(λ=0.5); ",
          "if MMR matches HCPC-v2, the diversification heuristic alone ",
          "is sufficient and HCPC-v2 adds no value beyond standard MMR. ",
          "If HCPC-v2 wins, the coherence-gating signal carries info ",
          "MMR's diversity penalty does not."]
    open(os.path.join(OUT_DIR, "summary.md"), "w").write("\n".join(md))
    print(f"\n[MMR] outputs -> {OUT_DIR}/")
    if not h.empty: print(h.to_string(index=False))


if __name__ == "__main__":
    main()
