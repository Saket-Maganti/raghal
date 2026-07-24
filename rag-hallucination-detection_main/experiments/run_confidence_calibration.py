"""
experiments/run_confidence_calibration.py — Phase 5 #9
======================================================

Does the model's *self-reported* confidence correlate with CCS?

Mechanism: after the normal answer call, we ask the same generator to
score its own confidence (0-100) in the answer it just gave, citing
the retrieved context. If self-confidence drops on low-CCS retrieval
sets, that's strong cross-signal evidence: the model itself "knows"
when the context is fragmented, and CCS is a proxy for that internal
signal.

Two correlation tests:
    Pearson r(ccs, self_confidence)        — linear
    Spearman ρ(ccs, self_confidence)       — rank-based, robust

Plus a per-quintile breakdown: hallucination rate by self-confidence
quintile, joined with hallucination rate by CCS quintile.

Output:
    results/confidence_calibration/per_query.csv      (one row per question)
    results/confidence_calibration/correlations.csv   (r, rho, p-values)
    results/confidence_calibration/quintile_table.csv (joint binning)
    results/confidence_calibration/summary.md

Run (Ollama):
    ollama serve &
    python3 experiments/run_confidence_calibration.py \\
        --datasets squad pubmedqa --n_questions 30
    # ~30 q × 2 datasets × 2 calls each (answer + confidence) × 3 s
    # = ~10 min on M4 (no condition sweep — single retrieval per query).

Run (Groq, free, ~3 min):
    export GROQ_API_KEY=...
    python3 experiments/run_confidence_calibration.py --backend groq \\
        --model llama-3.3-70b --datasets squad pubmedqa --n_questions 30
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from src.dataset_loaders        import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline           import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_v2_retriever      import HCPCv2Retriever

OUT_DIR = "results/confidence_calibration"
EMBED   = "sentence-transformers/all-MiniLM-L6-v2"

CONFIDENCE_PROMPT = (
    "Given the question, the context provided, and your previous answer, "
    "rate your confidence that your answer is fully supported by the "
    "context on a scale from 0 (not at all supported) to 100 (fully "
    "supported). Reply with ONLY a single integer between 0 and 100. "
    "No explanation, no other text.\n\n"
    "Question: {question}\n\n"
    "Context:\n{context}\n\n"
    "Your previous answer: {answer}\n\n"
    "Confidence (0-100):"
)


def _parse_confidence(text: str) -> float:
    """Pull the first integer 0-100 out of the model's reply."""
    if not text:
        return float("nan")
    m = re.search(r"\b(\d{1,3})\b", text)
    if not m:
        return float("nan")
    val = int(m.group(1))
    return float(min(100, max(0, val)))


def run(ds, n_q, backend, model, det):
    print(f"\n{'='*72}\n[Conf] {ds.upper()} × {backend}/{model}\n{'='*72}")
    docs, qa = load_dataset_by_name(ds, max_papers=30)
    if not docs or not qa: return []

    coll = f"conf_{ds}_{model.replace('-', '_').replace('.', '_').replace('/', '_')}"
    pipe = RAGPipeline(
        chunk_size=1024, chunk_overlap=100, top_k=3,
        model_name=model, embed_model=EMBED,
        persist_dir=f"./chroma_db_conf/{coll}",
    )
    pipe.index_documents(docs, collection_name=coll)

    if backend == "groq":
        from src.groq_llm import GroqLLM
        pipe.llm = GroqLLM(model=model, temperature=0.0)

    # Use HCPCv2 to get a meaningful CCS value per query
    retr = HCPCv2Retriever(pipeline=pipe, sim_threshold=0.45,
                            ce_threshold=-0.20,
                            top_k_protected=2, max_refine=2)

    rows = []
    for qa_pair in qa[:n_q]:
        try:
            ret_out = retr.retrieve(qa_pair["question"])
            chunks, hlog = ret_out if isinstance(ret_out, tuple) else (ret_out, {})
            gen = pipe.generate(qa_pair["question"], chunks)
            nli = det.detect(gen["answer"], gen["context"])

            # Second call: ask for confidence
            conf_prompt = CONFIDENCE_PROMPT.format(
                question=qa_pair["question"],
                context=gen["context"][:2000],
                answer=gen["answer"][:500],
            )
            conf_text = pipe.llm.invoke(conf_prompt)
            confidence = _parse_confidence(conf_text)

            rows.append({
                "dataset":            ds,
                "question":           qa_pair["question"],
                "answer":             gen["answer"],
                "ccs":                hlog.get("context_coherence", -1.0)
                                       if isinstance(hlog, dict) else -1.0,
                "faithfulness_score": nli["faithfulness_score"],
                "is_hallucination":   bool(nli["is_hallucination"]),
                "self_confidence":    confidence,
                "confidence_raw":     conf_text[:80],
            })
        except Exception as exc:
            print(f"[Conf] err: {exc}")
    return rows


def correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Pearson + Spearman of ccs vs self_confidence, per dataset and overall."""
    rows = []
    for label, sub in [("__all__", df)] + list(df.groupby("dataset")):
        if isinstance(label, tuple):
            label = label[0]
        clean = sub.dropna(subset=["ccs", "self_confidence"])
        clean = clean[clean["ccs"] >= 0]
        if len(clean) < 5:
            continue
        r,  p_r  = pearsonr(clean["ccs"], clean["self_confidence"])
        rho, p_s = spearmanr(clean["ccs"], clean["self_confidence"])
        rows.append({
            "dataset":   label,
            "n":         int(len(clean)),
            "pearson_r": round(float(r), 4),
            "pearson_p": round(float(p_r), 4),
            "spearman_rho": round(float(rho), 4),
            "spearman_p":   round(float(p_s), 4),
        })
    return pd.DataFrame(rows)


def quintile_table(df: pd.DataFrame, n_bins: int = 5) -> pd.DataFrame:
    """Hallucination rate by CCS quintile and by self-confidence quintile —
    side-by-side so we can see if both predict similarly."""
    df = df.copy()
    df = df[df["ccs"] >= 0].dropna(subset=["self_confidence"])
    if len(df) < n_bins * 3:
        return pd.DataFrame()
    df["ccs_q"] = pd.qcut(df["ccs"], q=n_bins, labels=False, duplicates="drop")
    df["conf_q"] = pd.qcut(df["self_confidence"], q=n_bins, labels=False,
                            duplicates="drop")
    out = []
    for q in sorted(df["ccs_q"].dropna().unique()):
        sub_ccs = df[df["ccs_q"] == q]
        sub_conf = df[df["conf_q"] == q]
        out.append({
            "quintile":         int(q) + 1,
            "ccs_mean":         round(sub_ccs["ccs"].mean(), 3),
            "ccs_halluc_rate":  round(sub_ccs["is_hallucination"].mean(), 4),
            "ccs_n":            len(sub_ccs),
            "conf_mean":        round(sub_conf["self_confidence"].mean(), 1),
            "conf_halluc_rate": round(sub_conf["is_hallucination"].mean(), 4),
            "conf_n":           len(sub_conf),
        })
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa"])
    ap.add_argument("--n_questions", type=int, default=30)
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
            print(f"[Conf] unknown dataset {ds}"); continue
        all_rows.extend(run(ds, args.n_questions, args.backend, args.model, det))

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUT_DIR, "per_query.csv"), index=False)
    print(f"\n[Conf] wrote {len(df)} rows.")

    if not df.empty:
        c = correlations(df); c.to_csv(os.path.join(OUT_DIR, "correlations.csv"), index=False)
        print("\n[Conf] correlations (CCS vs self-confidence):")
        print(c.to_string(index=False))

        q = quintile_table(df); q.to_csv(os.path.join(OUT_DIR, "quintile_table.csv"), index=False)
        print("\n[Conf] joint quintile table:")
        print(q.to_string(index=False))

        md = ["# Confidence calibration (Phase 5 #9)", "",
              f"Backend: {args.backend}, Model: {args.model}, n={len(df)}", "",
              "## Correlations", "",
              c.to_markdown(index=False) if not c.empty else "(no data)",
              "", "## Joint quintile breakdown", "",
              q.to_markdown(index=False) if not q.empty else "(no data)",
              "",
              "Reading: if pearson_r > 0.3 with p < 0.05, the model's "
              "self-reported confidence aligns with CCS — the LLM "
              "implicitly tracks coherence."]
        open(os.path.join(OUT_DIR, "summary.md"), "w").write("\n".join(md))

    print(f"\n[Conf] outputs -> {OUT_DIR}/")


if __name__ == "__main__":
    main()
