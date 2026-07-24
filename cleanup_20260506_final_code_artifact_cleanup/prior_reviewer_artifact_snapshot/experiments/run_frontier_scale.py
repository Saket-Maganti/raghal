"""
run_frontier_scale.py — Phase 2 Item 2 (frontier-scale ablation)
================================================================

Re-runs the baseline / HCPC-v1 / HCPC-v2 comparison on 70-B class models
(Llama-3.3-70B, Mixtral-8×7B) via Groq's free-tier API, to answer the
NeurIPS-level question:

    "Does the coherence paradox persist at frontier scale, or is it a
     small-model artifact?"

If the paradox magnitude (`faith_baseline − faith_hcpc_v1`) stays positive
at 70B on the same datasets where it holds at 7B, the paper's claim is
scale-robust.  If it vanishes, the paper must be re-framed as a
small-/medium-model phenomenon.

Design notes:
    • Retrieval + embedding stay local (MiniLM on M4/Kaggle) — only the
      generation LLM is swapped from Ollama Mistral-7B to Groq 70B.
    • Groq free tier is 30 RPM per model; the GroqLLM wrapper handles
      backoff.  30 q × 3 conditions × 2 datasets × 2 models ≈ 360 calls
      ≈ 12 min best case + backoff ≈ 30–45 min per model.
    • We skip HotpotQA by default to keep quotas tight; it can be added
      back via --datasets.

Requires:
    GROQ_API_KEY environment variable (free at console.groq.com).
    pip install groq

Outputs (results/frontier_scale/):
    per_query.csv           — one row per (dataset, model, condition, question)
    summary.csv             — aggregated per (dataset, model, condition)
    paradox_by_scale.csv    — paradox_drop / v2_recovery per (dataset, model)
                              joined against 7B Mistral reference for Δ
    summary.md              — narrative + tables for §Results

Run:
    export GROQ_API_KEY=...
    pip install groq
    python3 experiments/run_frontier_scale.py \
        --datasets squad pubmedqa \
        --models llama-3.3-70b mixtral-8x7b \
        --n_questions 30
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import os
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.retrieval_metrics import compute_retrieval_quality
from src.groq_llm import GroqLLM, GROQ_MODELS


OUTPUT_DIR = "results/frontier_scale"
CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, "completed_tuples.json")

CHUNK_SIZE   = 1024
TOP_K        = 3
EMBED_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"

V1_SIM = 0.50
V1_CE  = 0.00
V2_SIM = 0.45
V2_CE  = -0.20


def _load_checkpoint() -> Dict[str, bool]:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as fh:
            return json.load(fh)
    return {}


def _save_checkpoint(state: Dict[str, bool]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as fh:
        json.dump(state, fh, indent=2)


def _eval_query(
    pipeline: RAGPipeline,
    qa: Dict,
    retriever,
    label: str,
    detector: HallucinationDetector,
) -> Dict:
    if retriever is None:
        docs, _ = pipeline.retrieve_with_scores(qa["question"])
        hlog: Dict = {}
    else:
        out = retriever.retrieve(qa["question"])
        if isinstance(out, tuple):
            docs, hlog = out
        else:
            docs, hlog = out, {}

    gen = pipeline.generate(qa["question"], docs)
    nli = detector.detect(gen["answer"], gen["context"])
    ret_m = compute_retrieval_quality(qa["question"], docs, pipeline.embeddings)
    return {
        "question":            qa["question"],
        "ground_truth":        qa.get("ground_truth", ""),
        "answer":              gen["answer"],
        "condition":           label,
        "faithfulness_score":  nli["faithfulness_score"],
        "is_hallucination":    nli["is_hallucination"],
        "mean_retrieval_similarity": ret_m.get("mean_similarity", 0.0),
        "refined":             bool(hlog.get("refined", False))
                                if isinstance(hlog, dict) else False,
        "ccs":                 hlog.get("context_coherence", -1.0)
                                if isinstance(hlog, dict) else -1.0,
        "latency_s":           gen["latency_s"],
    }


def run_tuple(
    dataset: str,
    model_alias: str,
    n_questions: int,
    detector: HallucinationDetector,
) -> List[Dict]:
    print(f"\n{'='*72}\n[Frontier] {dataset.upper()} × {model_alias}\n{'='*72}")
    docs, qa = load_dataset_by_name(dataset, max_papers=30)
    if not docs or not qa:
        print(f"[Frontier] {dataset}: no data, skipping.")
        return []

    collection = f"frontier_{dataset}_{model_alias.replace('.', '_').replace('-', '_')}"
    # Build pipeline with Ollama *temporarily* to reuse the indexing +
    # retrieval path; then swap the LLM to Groq before generation.
    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=TOP_K,
        model_name="mistral",            # dummy; we replace .llm below
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_frontier/{collection}",
    )
    pipeline.index_documents(docs, collection_name=collection)

    # ── Swap in Groq LLM ──────────────────────────────────────────────
    pipeline.llm = GroqLLM(model=model_alias, temperature=0.1)
    pipeline.model_name = model_alias

    hcpc_v1 = HCPCRetriever(
        pipeline=pipeline,
        sim_threshold=V1_SIM, ce_threshold=V1_CE,
        top_k=TOP_K,
    )
    hcpc_v2 = HCPCv2Retriever(
        pipeline=pipeline,
        sim_threshold=V2_SIM, ce_threshold=V2_CE,
        top_k_protected=2, max_refine=2,
    )

    rows: List[Dict] = []
    for qa_pair in qa[:n_questions]:
        for label, retriever in [
            ("baseline", None),
            ("hcpc_v1",  hcpc_v1),
            ("hcpc_v2",  hcpc_v2),
        ]:
            try:
                rec = _eval_query(pipeline, qa_pair, retriever, label, detector)
                rec["dataset"] = dataset
                rec["model"]   = model_alias
                rows.append(rec)
            except Exception as exc:
                print(f"[Frontier] err {dataset}/{model_alias}/{label}: {exc}")
    return rows


def aggregate(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    grp = df.groupby(["dataset", "model", "condition"])
    summary = grp.agg(
        n_queries=("question", "count"),
        faith=("faithfulness_score", "mean"),
        halluc=("is_hallucination", "mean"),
        sim=("mean_retrieval_similarity", "mean"),
        refine_rate=("refined", "mean"),
        ccs=("ccs", lambda s: float(s[s >= 0].mean())
                              if (s >= 0).any() else float("nan")),
        latency=("latency_s", "mean"),
    ).reset_index()
    for c in ("faith", "halluc", "sim", "refine_rate", "ccs", "latency"):
        summary[c] = summary[c].round(4)
    return summary


def paradox_by_scale(
    summary: pd.DataFrame, ref_path: str = "results/multidataset/summary.csv",
) -> pd.DataFrame:
    if summary.empty:
        return summary
    ref = _load_reference_7b(ref_path)
    rows = []
    for (ds, mdl), sub in summary.groupby(["dataset", "model"]):
        try:
            base = sub[sub["condition"] == "baseline"].iloc[0]
            v1   = sub[sub["condition"] == "hcpc_v1"].iloc[0]
            v2   = sub[sub["condition"] == "hcpc_v2"].iloc[0]
        except IndexError:
            continue
        paradox_drop = round(base["faith"] - v1["faith"], 4)
        v2_recovery  = round(v2["faith"] - v1["faith"], 4)
        ref_par = ref.get((ds, "mistral"))
        rows.append({
            "dataset":            ds,
            "model":              mdl,
            "scale":              _scale_label(mdl),
            "faith_base":         base["faith"],
            "faith_v1":           v1["faith"],
            "faith_v2":           v2["faith"],
            "paradox_drop":       paradox_drop,
            "v2_recovery":        v2_recovery,
            "ref_paradox_7b":     ref_par,
            "delta_vs_7b":        (round(paradox_drop - ref_par, 4)
                                    if ref_par is not None else None),
            "paradox_persists":   (paradox_drop > 0.01),
        })
    return pd.DataFrame(rows)


def _scale_label(model_alias: str) -> str:
    a = model_alias.lower()
    if "120b" in a:
        return "120B"
    if "70b" in a:
        return "70B"
    if "32b" in a:
        return "32B"
    if "8x7b" in a or ("mixtral" in a and "8x" in a):
        return "8x7B"
    if "20b" in a:
        return "20B"
    if "17b" in a or "scout" in a:
        return "17B-MoE"
    if "9b" in a:
        return "9B"
    if "8b" in a:
        return "8B"
    return "?"


def _load_reference_7b(path: str) -> Dict[Tuple[str, str], float]:
    if not os.path.exists(path):
        return {}
    try:
        ref = pd.read_csv(path)
    except Exception:
        return {}
    out: Dict[Tuple[str, str], float] = {}
    for (ds, mdl), sub in ref.groupby(["dataset", "model"]):
        try:
            base = float(sub[sub["condition"] == "baseline"]["faith"].iloc[0])
            v1   = float(sub[sub["condition"] == "hcpc_v1"]["faith"].iloc[0])
        except (IndexError, KeyError):
            continue
        out[(ds, mdl)] = round(base - v1, 4)
    return out


def write_summary_md(
    summary: pd.DataFrame, paradox: pd.DataFrame, out_path: str,
) -> None:
    lines = [
        "# Frontier-scale ablation (Phase 2 Item 2)", "",
        "Re-runs the coherence-paradox comparison on 70-B class models via "
        "the Groq free-tier API.  The retrieval stack (MiniLM embeddings + "
        "HCPC retrievers) is unchanged; only the generation LLM is "
        "swapped from Ollama Mistral-7B to a larger model, so any "
        "difference in `paradox_drop` is attributable to scale.", "",
        "## Aggregated metrics", "",
        summary.to_markdown(index=False) if not summary.empty else "(no data)",
        "",
        "## Paradox vs 7B reference", "",
        "`ref_paradox_7b` = same-dataset paradox drop at Mistral-7B from "
        "`results/multidataset/summary.csv`.  `delta_vs_7b > 0` means the "
        "paradox grew at scale; `< 0` means it shrank.  "
        "`paradox_persists` = True if the 70B run still shows > 0.01 faith "
        "drop from baseline to HCPC-v1 — the canonical threshold for "
        "'the paradox is real at this scale.'", "",
        paradox.to_markdown(index=False) if not paradox.empty else "(no data)",
        "",
        "Target finding for NeurIPS: `paradox_persists == True` on at "
        "least one 70B row.  That rules out "
        "\"it's a small-model artifact\" as a reviewer critique.",
    ]
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa"])
    parser.add_argument("--models", nargs="+",
                        default=["llama-3.3-70b", "mixtral-8x7b"])
    parser.add_argument("--n_questions", type=int, default=30)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--ref_path", type=str,
                        default="results/multidataset/summary.csv")
    args = parser.parse_args()

    for m in args.models:
        if m not in GROQ_MODELS and m not in GROQ_MODELS.values():
            print(f"[Frontier] WARNING: {m} not in known Groq aliases "
                  f"{list(GROQ_MODELS)}.  Will try as full model id.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    state = _load_checkpoint()
    detector = HallucinationDetector()

    all_rows: List[Dict] = []
    prior = os.path.join(OUTPUT_DIR, "per_query.csv")
    if os.path.exists(prior):
        try:
            all_rows.extend(pd.read_csv(prior).to_dict("records"))
        except Exception:
            pass

    for ds in args.datasets:
        if ds not in DATASET_REGISTRY:
            print(f"[Frontier] unknown dataset {ds}, skipping")
            continue
        for mdl in args.models:
            key = f"{ds}__{mdl}"
            if state.get(key) and not args.force:
                print(f"[Frontier] checkpoint hit, skipping {key}")
                continue
            rows = run_tuple(ds, mdl, args.n_questions, detector)
            all_rows.extend(rows)
            pd.DataFrame(rows).to_csv(
                os.path.join(OUTPUT_DIR, f"{key.replace('.','_').replace('-','_')}_per_query.csv"),
                index=False,
            )
            state[key] = True
            _save_checkpoint(state)

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "per_query.csv"), index=False)
    summary = aggregate(all_rows)
    summary.to_csv(os.path.join(OUTPUT_DIR, "summary.csv"), index=False)
    paradox = paradox_by_scale(summary, args.ref_path)
    paradox.to_csv(os.path.join(OUTPUT_DIR, "paradox_by_scale.csv"), index=False)
    write_summary_md(summary, paradox, os.path.join(OUTPUT_DIR, "summary.md"))
    print(f"[Frontier] outputs -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
