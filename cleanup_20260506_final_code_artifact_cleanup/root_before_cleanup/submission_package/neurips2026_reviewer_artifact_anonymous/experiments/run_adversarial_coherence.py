"""
run_adversarial_coherence.py  — §7.6 Adversarial Coherence Failures
====================================================================

Evaluates three adversarial categories against a matched coherent control:

  (a) disjoint   — same entity, different surface forms across passages
  (b) contradict — opposing conclusions, all high query-similarity
  (c) drift      — progressively off-topic chain, each passage individually
                   passes a relevance threshold

For each case we:
  1. Embed passages, compute CCS, Jaccard, entropy, variance, sim_spread,
     mean query-chunk similarity.
  2. Run NLI-pairwise contradiction scoring across all passage pairs.
  3. Generate an answer with the configured LLM, then score NLI-faithfulness.
  4. Aggregate per-signal detection AUC (adversarial-vs-control) and
     per-category hallucination rates.

Outputs (results/adversarial/):
  per_case.csv          — one row per case with all signals + faithfulness
  detection_summary.csv — per-signal AUC, precision, recall against control
  category_summary.csv  — per-category aggregate metrics
  answers.jsonl         — full generated answers (for qualitative inspection)
  summary.md            — human-readable results digest

Runs on M4 laptop (no GPU required). Expect ~3-4 hours for 120 cases with
Ollama Mistral-7B.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import os
from dataclasses import asdict
from typing import Dict, List

import numpy as np
import pandas as pd

from src.adversarial_cases import load_all_cases, AdversarialCase
from src.coherence_metrics import compute_coherence_metrics, compute_nli_pairwise
from src.hallucination_detector import HallucinationDetector
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# ── Parameters ────────────────────────────────────────────────────────────────

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_NAME  = os.environ.get("ADV_MODEL", "mistral")
OUTPUT_DIR  = "results/adversarial"

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a helpful assistant that answers questions based ONLY on the provided context.\n"
        'If the answer is not in the context, say "I cannot find this information in the provided context."\n\n'
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer based strictly on the context above:"
    ),
)


# ── NLI wrapper used by compute_nli_pairwise ──────────────────────────────────

class _NLIPairwiseWrapper:
    """Exposes (premise, hypothesis) -> dict(entailment, neutral, contradiction)."""
    def __init__(self, detector: HallucinationDetector):
        self._det = detector

    def __call__(self, premise: str, hypothesis: str) -> Dict[str, float]:
        return self._det.score_sentence(premise, hypothesis)


# ── Main evaluation ───────────────────────────────────────────────────────────

def evaluate_case(
    case: AdversarialCase,
    embeddings,
    nli_pair_fn,
    detector: HallucinationDetector,
    llm: OllamaLLM,
) -> Dict:
    """Compute all signals + generate answer for a single case."""
    docs = case.as_documents()

    coh  = compute_coherence_metrics(case.query, docs, embeddings)
    nli_pw = compute_nli_pairwise(docs, nli_pair_fn)

    context = "\n\n---\n\n".join(d.page_content for d in docs)
    prompt  = RAG_PROMPT.format(context=context, question=case.query)

    try:
        answer = llm.invoke(prompt)
    except Exception as exc:
        answer = f"[GENERATION ERROR: {exc}]"

    nli = detector.detect(answer, context)

    record = {
        "case_id":            case.case_id,
        "category":           case.category,
        "query":              case.query,
        "gold_label":         case.gold_context_label,
        "reference_answer":   case.reference_answer,
        "answer":             answer,
        "faithfulness_score": nli["faithfulness_score"],
        "is_hallucination":   nli["is_hallucination"],
        # Coherence signals:
        "ccs":                 coh.get("ccs", -1.0),
        "ccs_mean":            coh.get("ccs_mean", -1.0),
        "ccs_std":             coh.get("ccs_std",  -1.0),
        "embedding_variance":  coh.get("embedding_variance", -1.0),
        "mean_jaccard":        coh.get("mean_jaccard", -1.0),
        "retrieval_entropy":   coh.get("retrieval_entropy", -1.0),
        "mean_query_chunk_sim": coh.get("mean_query_chunk_sim", -1.0),
        "sim_spread":          coh.get("sim_spread", -1.0),
        "nli_pair_mean":       nli_pw.get("nli_pairwise_mean", -1.0),
        "nli_pair_max":        nli_pw.get("nli_pairwise_max", -1.0),
        "nli_pair_frac_hi":    nli_pw.get("nli_pairwise_frac_hi", -1.0),
        # Construction metadata:
        "notes":               case.notes,
    }
    return record


def per_signal_detection_auc(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each adversarial category (disjoint/contradict/drift) vs control,
    compute detection AUC for each candidate signal. Higher-for-adversarial
    or lower-for-adversarial direction is determined per signal.
    """
    from sklearn.metrics import roc_auc_score

    # Signals oriented so that LOW = more coherent, HIGH = more adversarial.
    # For sim-like signals (ccs, mean_jaccard, mean_query_chunk_sim) we
    # negate so "higher = more adversarial".
    signals = {
        "mean_query_chunk_sim_neg": lambda r: -r,   # relevance-only baseline
        "ccs_neg":                  lambda r: -r,
        "mean_jaccard_neg":         lambda r: -r,
        "embedding_variance":       lambda r: r,
        "retrieval_entropy":        lambda r: r,
        "sim_spread":               lambda r: r,
        "nli_pair_mean":            lambda r: r,
        "nli_pair_max":             lambda r: r,
        "nli_pair_frac_hi":         lambda r: r,
    }
    # Source columns for negated variants:
    src_col = {
        "mean_query_chunk_sim_neg": "mean_query_chunk_sim",
        "ccs_neg":                  "ccs",
        "mean_jaccard_neg":         "mean_jaccard",
    }

    out_rows = []
    for adv_cat in ("disjoint", "contradict", "drift"):
        sub = df[df["category"].isin([adv_cat, "control"])].copy()
        if sub.empty or "control" not in sub["category"].values or adv_cat not in sub["category"].values:
            continue
        y = (sub["category"] == adv_cat).astype(int).values
        for sig_name, orient in signals.items():
            col = src_col.get(sig_name, sig_name)
            if col not in sub.columns:
                continue
            scores = sub[col].apply(orient).values
            mask = np.isfinite(scores) & (scores > -1.0)
            if mask.sum() < 4 or len(set(y[mask])) < 2:
                auc = np.nan
            else:
                try:
                    auc = float(roc_auc_score(y[mask], scores[mask]))
                except Exception:
                    auc = np.nan
            out_rows.append({
                "adversarial_category": adv_cat,
                "signal":               sig_name,
                "detection_auc":        round(auc, 4) if not np.isnan(auc) else None,
                "n":                    int(mask.sum()),
            })
    return pd.DataFrame(out_rows)


def category_summary(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby("category")
    rows = []
    for cat, sub in grp:
        rows.append({
            "category":                 cat,
            "n":                        len(sub),
            "hallucination_rate":       round(float(sub["is_hallucination"].mean()), 4),
            "mean_faithfulness":        round(float(sub["faithfulness_score"].mean()), 4),
            "mean_query_chunk_sim":     round(float(sub["mean_query_chunk_sim"].mean()), 4),
            "mean_ccs":                 round(float(sub["ccs"].mean()), 4),
            "mean_jaccard":             round(float(sub["mean_jaccard"].mean()), 4),
            "mean_embedding_variance":  round(float(sub["embedding_variance"].mean()), 4),
            "mean_retrieval_entropy":   round(float(sub["retrieval_entropy"].mean()), 4),
            "mean_sim_spread":          round(float(sub["sim_spread"].mean()), 4),
            "mean_nli_pair_mean":       round(float(sub["nli_pair_mean"].mean()), 4),
            "mean_nli_pair_frac_hi":    round(float(sub["nli_pair_frac_hi"].mean()), 4),
        })
    return pd.DataFrame(rows)


def write_summary_md(cat_df: pd.DataFrame, det_df: pd.DataFrame, out_path: str) -> None:
    lines = ["# Adversarial Coherence — Summary", "", "## Per-category aggregates", ""]
    lines.append(cat_df.to_markdown(index=False))
    lines.append("")
    lines.append("## Per-signal detection AUC (adversarial vs control)")
    lines.append("")
    lines.append(det_df.to_markdown(index=False))
    lines.append("")
    lines.append("> Signals with `_neg` suffix are negated so 'higher = more adversarial'.")
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("[Adv] Loading cases...")
    cases_by_cat = load_all_cases()
    for cat, cases in cases_by_cat.items():
        print(f"  {cat}: {len(cases)} cases")

    print(f"[Adv] Loading embeddings: {EMBED_MODEL}")
    import torch as _torch
    _dev = "cuda" if _torch.cuda.is_available() else (
        "mps" if getattr(_torch.backends, "mps", None) and _torch.backends.mps.is_available() else "cpu"
    )
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": _dev},
    )

    print("[Adv] Loading NLI detector...")
    detector = HallucinationDetector()
    nli_pair_fn = _NLIPairwiseWrapper(detector)

    print(f"[Adv] Connecting to Ollama ({MODEL_NAME})")
    llm = OllamaLLM(model=MODEL_NAME, temperature=0.1)

    # ── Run ────────────────────────────────────────────────────────────────
    records: List[Dict] = []
    for cat in ("disjoint", "contradict", "drift", "control"):
        for case in cases_by_cat.get(cat, []):
            print(f"[Adv] {case.case_id} ({cat})")
            rec = evaluate_case(case, embeddings, nli_pair_fn, detector, llm)
            records.append(rec)

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(OUTPUT_DIR, "per_case.csv"), index=False)

    # Save full answers for qualitative review
    with open(os.path.join(OUTPUT_DIR, "answers.jsonl"), "w") as fh:
        for r in records:
            fh.write(json.dumps({
                "case_id": r["case_id"],
                "category": r["category"],
                "query":   r["query"],
                "reference_answer": r["reference_answer"],
                "answer":  r["answer"],
                "faithfulness_score": r["faithfulness_score"],
                "is_hallucination":   r["is_hallucination"],
            }) + "\n")

    cat_df = category_summary(df)
    cat_df.to_csv(os.path.join(OUTPUT_DIR, "category_summary.csv"), index=False)

    det_df = per_signal_detection_auc(df)
    det_df.to_csv(os.path.join(OUTPUT_DIR, "detection_summary.csv"), index=False)

    write_summary_md(
        cat_df, det_df,
        os.path.join(OUTPUT_DIR, "summary.md"),
    )
    print(f"[Adv] Outputs -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
