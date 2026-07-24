"""
experiments/run_synthetic_causal.py — Phase 7 #1
=================================================

Causal experiment isolating coherence from per-passage similarity.

The reviewer challenge: existing evidence is correlational. To establish
causality we need an INTERVENTION — construct retrieval sets where
similarity is held fixed and only coherence varies, then show
faithfulness tracks coherence.

Design:
    For each query Q, collect 6+ retrieved candidate passages
    sorted by query similarity. Build two matched sets of size k=3:

        SET-A (coherent):    top-1 passage  +  top-2 passage  +  top-3 passage
                              (all about the same Q topic; high CCS)
        SET-B (incoherent): top-1 passage  +  random off-topic passage
                              from a different query, sim-matched to top-2,
                              + another random off-topic passage sim-matched
                              to top-3
                              (mean similarity matches SET-A within ε,
                              but CCS is much lower)

    SET-A and SET-B have *matched* mean retrieval similarity (within
    a small tolerance). They differ in CCS by construction. Run the
    generator on each and measure faithfulness.

If the coherence account is causal: SET-B faithfulness < SET-A
faithfulness with statistical significance, even though per-passage
similarity is matched.

If similarity is the only relevant signal: both should produce equal
faithfulness.

Outputs:
    results/synthetic_causal/per_query.csv  (one row per query × set type)
    results/synthetic_causal/summary.csv    (mean faith / halluc / CCS by set)
    results/synthetic_causal/paired_test.csv (Wilcoxon signed-rank stats)
    results/synthetic_causal/summary.md     (narrative + table)

Run (Ollama, ~2 hr local Mac for 100 queries):
    ollama serve &
    python3 experiments/run_synthetic_causal.py \\
        --datasets squad pubmedqa --n 100 --backend ollama --model mistral

Run (Groq, ~10 min, Kaggle-friendly):
    export GROQ_API_KEY=...
    python3 experiments/run_synthetic_causal.py \\
        --backend groq --model llama-3.3-70b --n 100

Statistical significance:
    Per (dataset), pair-up SET-A and SET-B faithfulness scores by
    query and run a paired Wilcoxon signed-rank test. p < 0.05 means
    coherence has a causal effect on faithfulness at fixed similarity.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

# When running with --backend groq we never call Ollama, but
# RAGPipeline.__init__ instantiates OllamaLLM which can hang on Kaggle
# (no local daemon to connect to). Monkey-patch OllamaLLM with a stub
# BEFORE importing RAGPipeline so the constructor returns instantly.
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

OUT_DIR = "results/synthetic_causal"
EMBED   = "sentence-transformers/all-MiniLM-L6-v2"
SIM_TOL = 0.10      # mean-similarity match tolerance between SET-A and SET-B
                    # (was 0.05 — too strict for finite pools; 0.10 still
                    # gives a meaningful matched comparison)


def _embed(texts, embedder):
    """Wrapper that handles either a langchain HuggingFaceEmbeddings instance
    or a sentence-transformers SentenceTransformer."""
    return np.array(embedder.embed_documents(list(texts)))


def _ccs(emb_matrix: np.ndarray) -> float:
    """CCS = mean(off-diag pairwise cos) − std(off-diag pairwise cos)."""
    if len(emb_matrix) < 2:
        return 1.0
    norm = np.linalg.norm(emb_matrix, axis=1, keepdims=True) + 1e-12
    E = emb_matrix / norm
    sims = E @ E.T
    iu = np.triu_indices(len(sims), k=1)
    pair = sims[iu]
    return float(pair.mean() - pair.std())


def _mean_sim_to_query(query_emb, doc_embs):
    norm_q = query_emb / (np.linalg.norm(query_emb) + 1e-12)
    norm_d = doc_embs / (np.linalg.norm(doc_embs, axis=1, keepdims=True) + 1e-12)
    return float((norm_d @ norm_q).mean())


def _construct_pair(query: str, candidates: List[Any], pool: List[Any],
                     embedder) -> Tuple[List[Any], List[Any], Dict]:
    """Construct matched (coherent, incoherent) pair for one query.

    Returns (set_a, set_b, diagnostics) where set_a = top-3 candidates
    and set_b = top-1 + 2 sim-matched off-topic passages from `pool`.
    """
    if len(candidates) < 3 or len(pool) < 5:
        return None, None, {"reason": "insufficient_candidates_or_pool",
                              "n_candidates": len(candidates),
                              "n_pool": len(pool)}

    # Embed query + candidates
    q_emb = np.array(embedder.embed_query(query))
    cand_texts = [c.page_content for c in candidates[:6]]
    cand_embs = _embed(cand_texts, embedder)
    cand_sims = (cand_embs / (np.linalg.norm(cand_embs, axis=1, keepdims=True) + 1e-12)
                 ) @ (q_emb / (np.linalg.norm(q_emb) + 1e-12))

    set_a = candidates[:3]
    a_embs = cand_embs[:3]
    target_sim_2 = float(cand_sims[1])
    target_sim_3 = float(cand_sims[2])

    # Build pool embeddings (subsample for speed)
    pool_sample = random.sample(pool, min(len(pool), 200))
    pool_texts = [p.page_content for p in pool_sample]
    pool_embs = _embed(pool_texts, embedder)
    pool_norm = pool_embs / (np.linalg.norm(pool_embs, axis=1, keepdims=True) + 1e-12)
    pool_sims = pool_norm @ (q_emb / (np.linalg.norm(q_emb) + 1e-12))

    # Find pool passages sim-matched to target_sim_2 and target_sim_3
    def _find_matched(target):
        diffs = np.abs(pool_sims - target)
        idx = int(np.argmin(diffs))
        return idx, float(diffs[idx])

    idx_2, diff_2 = _find_matched(target_sim_2)
    # Mask out idx_2 then find next match
    pool_sims_masked = pool_sims.copy()
    pool_sims_masked[idx_2] = -np.inf
    idx_3, diff_3 = _find_matched(target_sim_3)

    if max(diff_2, diff_3) > SIM_TOL:
        return None, None, {"reason": "no_matched_pool_passages",
                              "diff_2": diff_2, "diff_3": diff_3}

    set_b = [candidates[0], pool_sample[idx_2], pool_sample[idx_3]]
    b_embs = np.vstack([cand_embs[0], pool_embs[idx_2], pool_embs[idx_3]])

    return set_a, set_b, {
        "ccs_a":          _ccs(a_embs),
        "ccs_b":          _ccs(b_embs),
        "mean_sim_a":     _mean_sim_to_query(q_emb, a_embs),
        "mean_sim_b":     _mean_sim_to_query(q_emb, b_embs),
        "match_diff":     max(diff_2, diff_3),
    }


def _make_llm(backend: str, model: str):
    if backend == "groq":
        from src.groq_llm import GroqLLM
        return GroqLLM(model=model, temperature=0.0)
    from langchain_ollama import OllamaLLM
    return OllamaLLM(model=model, temperature=0.0)


def run(dataset: str, n_queries: int, backend: str, model: str,
        det: HallucinationDetector) -> List[Dict]:
    print(f"\n[Causal] {dataset.upper()} × {backend}/{model} × n={n_queries}")
    docs, qa = load_dataset_by_name(dataset, max_papers=30)
    if not docs or not qa:
        return []

    coll = f"causal_{dataset}_{model.replace('/', '_').replace('-', '_').replace('.', '_')}"
    pipe = RAGPipeline(
        chunk_size=1024, chunk_overlap=100, top_k=6,
        model_name=model, embed_model=EMBED,
        persist_dir=f"./chroma_db_causal/{coll}",
    )
    pipe.index_documents(docs, collection_name=coll)
    pipe.llm = _make_llm(backend, model)
    embedder = pipe.embeddings

    # Build an off-topic pool ONCE: pull top-20 chunks for ~30 sample
    # queries and dedup by content. This typically yields 100-400 unique
    # chunks. Reduced from top_k=50 × 100 queries (which was way overkill
    # and slow on Kaggle).
    pool_query_step = max(1, len(qa) // 30)
    pool_query_indices = list(range(0, len(qa), pool_query_step))[:30]
    print(f"[Causal/{dataset}] building off-topic pool from "
          f"{len(pool_query_indices)} queries × top-20 …", flush=True)
    original_k = pipe.top_k
    pipe.top_k = 20
    try:
        pool_seen = set()
        large_pool: List[Any] = []
        for i, q_idx in enumerate(pool_query_indices):
            try:
                pool_chunk, _ = pipe.retrieve_with_scores(qa[q_idx]["question"])
            except Exception as exc:
                print(f"[Causal/{dataset}]   pool query {i} err: {exc}",
                      flush=True)
                continue
            new = 0
            for d in pool_chunk:
                k = d.page_content[:200]
                if k in pool_seen: continue
                pool_seen.add(k); large_pool.append(d); new += 1
            if (i + 1) % 5 == 0:
                print(f"[Causal/{dataset}]   pool: {i+1}/{len(pool_query_indices)} "
                      f"queries, {len(large_pool)} unique chunks so far",
                      flush=True)
        print(f"[Causal/{dataset}] FINAL pool size = {len(large_pool)} "
              "unique chunks", flush=True)
    finally:
        pipe.top_k = original_k

    # Now request 6 candidates per query (need top-6 for set_a + matching)
    pipe.top_k = 6
    rows: List[Dict] = []
    n_processed = 0
    n_skipped = 0
    skip_reasons: Dict[str, int] = {}
    for qa_pair in qa:
        if n_processed >= n_queries:
            break
        try:
            cands, _ = pipe.retrieve_with_scores(qa_pair["question"])
            if len(cands) < 6:
                n_skipped += 1
                skip_reasons["fewer_than_6_candidates"] = skip_reasons.get(
                    "fewer_than_6_candidates", 0) + 1
                continue
            # Off-topic pool = the large pool, minus this query's own
            # top candidates (so we don't accidentally re-include them)
            cand_keys = {c.page_content[:200] for c in cands}
            pool = [d for d in large_pool if d.page_content[:200] not in cand_keys]
            set_a, set_b, diag = _construct_pair(qa_pair["question"],
                                                   cands[:6], pool, embedder)
            if set_a is None:
                n_skipped += 1
                reason = diag.get("reason", "unknown") if isinstance(diag, dict) else "unknown"
                skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
                continue

            # Generate on each set
            for label, docs_set in [("set_a_coherent", set_a),
                                      ("set_b_incoherent", set_b)]:
                gen = pipe.generate(qa_pair["question"], docs_set)
                nli = det.detect(gen["answer"], gen["context"])
                rows.append({
                    "dataset":          dataset,
                    "question":         qa_pair["question"],
                    "set_type":         label,
                    "ccs":              diag[f"ccs_{label[4]}"],
                    "mean_sim":         diag[f"mean_sim_{label[4]}"],
                    "faithfulness":     nli["faithfulness_score"],
                    "is_hallucination": nli["is_hallucination"],
                    "answer":           gen["answer"],
                    "ground_truth":     qa_pair.get("ground_truth", ""),
                    "match_diff":       diag["match_diff"],
                })
            n_processed += 1
            if n_processed % 5 == 0 or n_processed <= 3:
                print(f"  [Causal/{dataset}] {n_processed}/{n_queries} done",
                      flush=True)
        except Exception as exc:
            print(f"[Causal] err: {exc}")
            n_skipped += 1
    print(f"[Causal/{dataset}] processed={n_processed}  skipped={n_skipped}")
    if skip_reasons:
        print(f"[Causal/{dataset}] skip reasons: {skip_reasons}")
    return rows


def aggregate(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty: return df
    g = df.groupby(["dataset", "set_type"])
    s = g.agg(
        n=("question", "count"),
        faith=("faithfulness", "mean"),
        halluc=("is_hallucination", "mean"),
        ccs=("ccs", "mean"),
        mean_sim=("mean_sim", "mean"),
    ).reset_index()
    for c in ("faith", "halluc", "ccs", "mean_sim"):
        s[c] = s[c].round(4)
    return s


def paired_test(df: pd.DataFrame) -> pd.DataFrame:
    """Per-dataset, paired Wilcoxon signed-rank on (set_a, set_b) faith."""
    if df.empty or "dataset" not in df.columns:
        return pd.DataFrame()
    rows = []
    for ds, sub in df.groupby("dataset"):
        a = sub[sub["set_type"] == "set_a_coherent"].set_index("question")["faithfulness"]
        b = sub[sub["set_type"] == "set_b_incoherent"].set_index("question")["faithfulness"]
        common = a.index.intersection(b.index)
        if len(common) < 5:
            continue
        a, b = a.loc[common], b.loc[common]
        try:
            stat, p = wilcoxon(a.values, b.values, alternative="greater")
        except Exception as exc:
            print(f"[wilcoxon] {ds}: {exc}"); continue
        rows.append({
            "dataset":         ds,
            "n_pairs":         int(len(common)),
            "mean_faith_a":    round(float(a.mean()), 4),
            "mean_faith_b":    round(float(b.mean()), 4),
            "delta_faith":     round(float(a.mean() - b.mean()), 4),
            "wilcoxon_stat":   round(float(stat), 4),
            "wilcoxon_p":      round(float(p), 6),
            "causal_significant": bool(p < 0.05),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa"])
    ap.add_argument("--n", type=int, default=100,
                    help="number of queries per dataset")
    ap.add_argument("--backend", choices=["ollama", "groq"], default="ollama")
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if args.model is None:
        args.model = "mistral" if args.backend == "ollama" else "llama-3.3-70b"
    random.seed(args.seed)
    np.random.seed(args.seed)

    os.makedirs(OUT_DIR, exist_ok=True)
    det = HallucinationDetector()

    all_rows: List[Dict] = []
    for ds in args.datasets:
        if ds not in DATASET_REGISTRY:
            print(f"[Causal] unknown dataset {ds}"); continue
        all_rows.extend(run(ds, args.n, args.backend, args.model, det))

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUT_DIR, "per_query.csv"), index=False)
    s = aggregate(all_rows)
    s.to_csv(os.path.join(OUT_DIR, "summary.csv"), index=False)
    p = paired_test(df)
    p.to_csv(os.path.join(OUT_DIR, "paired_test.csv"), index=False)

    md = ["# Synthetic causal experiment (Phase 7 #1)", "",
          "Tests whether coherence has a *causal* effect on faithfulness ",
          "by constructing matched-similarity retrieval sets that differ ",
          "only in coherence (CCS).", "",
          "## Aggregated metrics by set type", "",
          s.to_markdown(index=False) if not s.empty else "(no data)", "",
          "## Paired Wilcoxon signed-rank test (per dataset)", "",
          p.to_markdown(index=False) if not p.empty else "(no data)", "",
          "Reading: causal_significant=True at $p < 0.05$ means coherence ",
          "has a causal effect on faithfulness *holding similarity fixed*."]
    open(os.path.join(OUT_DIR, "summary.md"), "w").write("\n".join(md))
    print(f"\n[Causal] outputs -> {OUT_DIR}/")
    if not p.empty:
        print(p.to_string(index=False))


if __name__ == "__main__":
    main()
