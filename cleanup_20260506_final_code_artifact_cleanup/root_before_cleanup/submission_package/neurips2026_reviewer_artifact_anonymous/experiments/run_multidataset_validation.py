"""
run_multidataset_validation.py — A1 (5-dataset validation) + A3 (3-model)
==========================================================================

Replicates Phase 6 (baseline / HCPC-v1 / HCPC-v2) across 6 datasets and 3
generators. Produces the expanded Table 2 reported in §Results.

Datasets   : squad, pubmedqa, naturalqs, triviaqa, hotpotqa, financebench
Generators : mistral, llama3, qwen2.5  (any subset via --models)

Per (dataset, model, condition) cell we record:
    nli_faithfulness, hallucination_rate, mean_retrieval_similarity,
    refinement_rate, mean_ccs

The runner is checkpoint-friendly: each (dataset, model) tuple writes its
own per_query.csv, so partial runs can be resumed by skipping completed
tuples (presence-of-output-file check).

Outputs (results/multidataset/):
    per_query.csv          — concatenated, all (dataset, model, condition)
    summary.csv            — aggregated per (dataset, model, condition)
    coherence_paradox.csv  — per-(dataset, model): faithfulness baseline-vs-v1
    summary.md             — markdown table for paper §Results
    completed_tuples.json  — checkpoint index

Run:
    python3 experiments/run_multidataset_validation.py \
        --datasets squad pubmedqa naturalqs triviaqa hotpotqa \
        --models mistral llama3 qwen2.5 \
        --n_questions 30
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import os
from typing import Dict, List, Tuple

import pandas as pd

from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.retrieval_metrics import compute_retrieval_quality

OUTPUT_DIR = "results/multidataset"
CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, "completed_tuples.json")

DEFAULT_DATASETS = ["squad", "pubmedqa", "naturalqs", "triviaqa", "hotpotqa", "financebench"]
DEFAULT_MODELS   = ["mistral", "llama3", "qwen2.5"]

V1_SIM_THRESHOLD  = 0.50
V1_CE_THRESHOLD   = 0.00
V2_SIM_THRESHOLD  = 0.45
V2_CE_THRESHOLD   = -0.20

CHUNK_SIZE = 1024
TOP_K      = 3
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _load_checkpoint() -> Dict[str, bool]:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as fh:
            return json.load(fh)
    return {}


def _save_checkpoint(state: Dict[str, bool]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as fh:
        json.dump(state, fh, indent=2)


def _eval_one_query(
    pipeline, qa, retriever, label, detector,
) -> Dict:
    if retriever is None:
        docs, sims = pipeline.retrieve_with_scores(qa["question"])
        hlog = {}
    else:
        out = retriever.retrieve(qa["question"])
        if isinstance(out, tuple):
            docs, hlog = out
        else:
            docs, hlog = out, {}
        sims = []
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
        "refined":             bool(hlog.get("refined", False)) if isinstance(hlog, dict) else False,
        "ccs":                 hlog.get("context_coherence", -1.0) if isinstance(hlog, dict) else -1.0,
    }


def run_one_tuple(
    dataset: str,
    model: str,
    n_questions: int,
    detector: HallucinationDetector,
) -> List[Dict]:
    """Run baseline / hcpc_v1 / hcpc_v2 on one (dataset, model) pair."""
    print(f"\n{'='*72}\n[MD] {dataset.upper()} × {model}\n{'='*72}")
    docs, qa = load_dataset_by_name(dataset, max_papers=30)
    if not docs or not qa:
        print(f"[MD] {dataset}: no data, skipping.")
        return []

    collection_name = f"md_{dataset}_{model}"
    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=TOP_K,
        model_name=model,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_md/{collection_name}",
    )
    pipeline.index_documents(docs, collection_name=collection_name)

    hcpc_v1 = HCPCRetriever(
        pipeline=pipeline,
        sim_threshold=V1_SIM_THRESHOLD,
        ce_threshold=V1_CE_THRESHOLD,
        sub_chunk_size=256,
        sub_chunk_overlap=32,
        top_k=TOP_K,
    )
    hcpc_v2 = HCPCv2Retriever(
        pipeline=pipeline,
        sim_threshold=V2_SIM_THRESHOLD,
        ce_threshold=V2_CE_THRESHOLD,
        top_k_protected=2,
        max_refine=2,
        sub_chunk_size=256,
        sub_chunk_overlap=32,
    )

    rows: List[Dict] = []
    for qa_pair in qa[:n_questions]:
        for label, retriever in [
            ("baseline", None),
            ("hcpc_v1",  hcpc_v1),
            ("hcpc_v2",  hcpc_v2),
        ]:
            try:
                rec = _eval_one_query(pipeline, qa_pair, retriever, label, detector)
                rec["dataset"] = dataset
                rec["model"]   = model
                rows.append(rec)
            except Exception as exc:
                print(f"[MD] error {dataset}/{model}/{label}: {exc}")
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
        ccs=("ccs", lambda s: float(s[s >= 0].mean()) if (s >= 0).any() else float("nan")),
    ).reset_index()
    for col in ["faith", "halluc", "sim", "refine_rate", "ccs"]:
        summary[col] = summary[col].round(4)
    return summary


def coherence_paradox_table(summary: pd.DataFrame) -> pd.DataFrame:
    """For each (dataset, model), report baseline-vs-v1 faithfulness gap."""
    if summary.empty:
        return summary
    rows = []
    for (ds, mdl), sub in summary.groupby(["dataset", "model"]):
        try:
            base = sub[sub["condition"] == "baseline"].iloc[0]
            v1   = sub[sub["condition"] == "hcpc_v1"].iloc[0]
            v2   = sub[sub["condition"] == "hcpc_v2"].iloc[0]
        except IndexError:
            continue
        rows.append({
            "dataset":   ds,
            "model":     mdl,
            "faith_baseline": base["faith"],
            "faith_v1":  v1["faith"],
            "faith_v2":  v2["faith"],
            "paradox_drop": round(base["faith"] - v1["faith"], 4),
            "v2_recovery":  round(v2["faith"] - v1["faith"], 4),
            "halluc_baseline": base["halluc"],
            "halluc_v1": v1["halluc"],
            "halluc_v2": v2["halluc"],
        })
    return pd.DataFrame(rows)


def write_summary_md(summary: pd.DataFrame, paradox: pd.DataFrame, out_path: str) -> None:
    lines = ["# Multi-dataset / multi-model validation", "", "## Aggregated metrics", ""]
    lines.append(summary.to_markdown(index=False) if not summary.empty else "(no data)")
    lines.append("")
    lines.append("## Coherence paradox per (dataset, model)")
    lines.append("`paradox_drop` = faith_baseline − faith_v1 (positive = paradox confirmed)")
    lines.append("`v2_recovery` = faith_v2 − faith_v1   (positive = v2 helps)")
    lines.append("")
    lines.append(paradox.to_markdown(index=False) if not paradox.empty else "(no data)")
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=DEFAULT_DATASETS)
    parser.add_argument("--models",   nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--n_questions", type=int, default=30)
    parser.add_argument("--force", action="store_true",
                        help="Re-run already-completed (dataset,model) tuples.")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    state = _load_checkpoint()
    detector = HallucinationDetector()

    all_rows: List[Dict] = []
    # Pull in any rows from prior partial runs so the consolidated CSV stays whole.
    prior_path = os.path.join(OUTPUT_DIR, "per_query.csv")
    if os.path.exists(prior_path):
        try:
            all_rows.extend(pd.read_csv(prior_path).to_dict("records"))
        except Exception:
            pass

    for ds in args.datasets:
        if ds not in DATASET_REGISTRY:
            print(f"[MD] unknown dataset {ds}, skipping")
            continue
        for mdl in args.models:
            key = f"{ds}__{mdl}"
            if state.get(key) and not args.force:
                print(f"[MD] checkpoint hit, skipping {key}")
                continue
            tuple_rows = run_one_tuple(ds, mdl, args.n_questions, detector)
            all_rows.extend(tuple_rows)
            # Per-tuple checkpoint
            pd.DataFrame(tuple_rows).to_csv(
                os.path.join(OUTPUT_DIR, f"{key}_per_query.csv"), index=False
            )
            state[key] = True
            _save_checkpoint(state)

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "per_query.csv"), index=False)
    summary = aggregate(all_rows)
    summary.to_csv(os.path.join(OUTPUT_DIR, "summary.csv"), index=False)
    paradox = coherence_paradox_table(summary)
    paradox.to_csv(os.path.join(OUTPUT_DIR, "coherence_paradox.csv"), index=False)
    write_summary_md(summary, paradox, os.path.join(OUTPUT_DIR, "summary.md"))
    print(f"[MD] outputs -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
