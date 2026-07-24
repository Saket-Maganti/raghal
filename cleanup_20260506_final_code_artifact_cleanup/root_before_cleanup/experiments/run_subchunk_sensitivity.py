"""
run_subchunk_sensitivity.py — Item 7 (Upgrade Wave 1b)
======================================================

Sweeps HCPC-v2's internal sub-chunk size over {128, 256, 512} tokens to
characterize the method's sensitivity to its own hyperparameter.

For each (dataset, sub_chunk_size) we re-run HCPC-v2 (and a fixed
baseline + HCPC-v1 reference) on the same 30-question subset and record
faithfulness, hallucination rate, refinement rate, and mean CCS.

The goal is a robustness plot / table for §Ablations showing that the
coherence paradox and v2 recovery are not an artifact of one specific
sub-chunk setting.

Outputs (results/subchunk_sensitivity/):
  per_query.csv        — per (dataset, sub_chunk, condition, question) row
  summary.csv          — aggregated per (dataset, sub_chunk, condition)
  paradox_by_sub.csv   — per (dataset, sub_chunk): paradox_drop, v2_recovery
  summary.md           — headline table

Run:
    python3 experiments/run_subchunk_sensitivity.py \
        --datasets squad pubmedqa \
        --model mistral \
        --n_questions 30 \
        --sub_chunks 128 256 512
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import os
from typing import Dict, List

import pandas as pd

from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.retrieval_metrics import compute_retrieval_quality


OUTPUT_DIR = "results/subchunk_sensitivity"
CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, "completed_tuples.json")

V1_SIM = 0.50
V1_CE  = 0.00
V2_SIM = 0.45
V2_CE  = -0.20

CHUNK_SIZE   = 1024
TOP_K        = 3
EMBED_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"


def _load_checkpoint() -> Dict[str, bool]:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as fh:
            return json.load(fh)
    return {}


def _save_checkpoint(state: Dict[str, bool]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as fh:
        json.dump(state, fh, indent=2)


def _eval_query(pipeline, qa, retriever, label, detector) -> Dict:
    if retriever is None:
        docs, _ = pipeline.retrieve_with_scores(qa["question"])
        hlog = {}
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
        "refined":             bool(hlog.get("refined", False)) if isinstance(hlog, dict) else False,
        "ccs":                 hlog.get("context_coherence", -1.0) if isinstance(hlog, dict) else -1.0,
    }


def run_tuple(
    dataset: str,
    sub_chunk: int,
    model: str,
    n_questions: int,
    detector: HallucinationDetector,
) -> List[Dict]:
    """Run baseline / hcpc_v1 / hcpc_v2 at a given sub_chunk setting."""
    print(f"\n{'='*72}\n[SubChunk] {dataset.upper()}  sub_chunk={sub_chunk}\n{'='*72}")
    docs, qa = load_dataset_by_name(dataset, max_papers=30)
    if not docs or not qa:
        print(f"[SubChunk] {dataset}: no data, skipping.")
        return []

    collection_name = f"sub_{dataset}_{sub_chunk}_{model}"
    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=TOP_K,
        model_name=model,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_sub/{collection_name}",
    )
    pipeline.index_documents(docs, collection_name=collection_name)

    hcpc_v1 = HCPCRetriever(
        pipeline=pipeline,
        sim_threshold=V1_SIM, ce_threshold=V1_CE,
        sub_chunk_size=sub_chunk,
        sub_chunk_overlap=max(16, sub_chunk // 8),
        top_k=TOP_K,
    )
    hcpc_v2 = HCPCv2Retriever(
        pipeline=pipeline,
        sim_threshold=V2_SIM, ce_threshold=V2_CE,
        top_k_protected=2, max_refine=2,
        sub_chunk_size=sub_chunk,
        sub_chunk_overlap=max(16, sub_chunk // 8),
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
                rec["dataset"]   = dataset
                rec["sub_chunk"] = sub_chunk
                rec["model"]     = model
                rows.append(rec)
            except Exception as exc:
                print(f"[SubChunk] err {dataset}/{sub_chunk}/{label}: {exc}")
    return rows


def aggregate(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    grp = df.groupby(["dataset", "sub_chunk", "condition"])
    summary = grp.agg(
        n_queries=("question", "count"),
        faith=("faithfulness_score", "mean"),
        halluc=("is_hallucination", "mean"),
        sim=("mean_retrieval_similarity", "mean"),
        refine_rate=("refined", "mean"),
        ccs=("ccs", lambda s: float(s[s >= 0].mean()) if (s >= 0).any() else float("nan")),
    ).reset_index()
    for c in ("faith", "halluc", "sim", "refine_rate", "ccs"):
        summary[c] = summary[c].round(4)
    return summary


def paradox_table(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return summary
    rows = []
    for (ds, sc), sub in summary.groupby(["dataset", "sub_chunk"]):
        try:
            base = sub[sub["condition"] == "baseline"].iloc[0]
            v1   = sub[sub["condition"] == "hcpc_v1"].iloc[0]
            v2   = sub[sub["condition"] == "hcpc_v2"].iloc[0]
        except IndexError:
            continue
        rows.append({
            "dataset":      ds,
            "sub_chunk":    sc,
            "faith_base":   base["faith"],
            "faith_v1":     v1["faith"],
            "faith_v2":     v2["faith"],
            "paradox_drop": round(base["faith"] - v1["faith"], 4),
            "v2_recovery":  round(v2["faith"] - v1["faith"], 4),
            "halluc_base":  base["halluc"],
            "halluc_v2":    v2["halluc"],
            "refine_rate":  v2["refine_rate"],
        })
    return pd.DataFrame(rows)


def write_summary_md(summary: pd.DataFrame, paradox: pd.DataFrame, out_path: str) -> None:
    lines = [
        "# HCPC-v2 sub-chunk sensitivity (Upgrade Item 7)", "",
        "Sweeping the internal sub-chunk size over {128, 256, 512} tokens "
        "to test whether the coherence paradox and v2 recovery depend on "
        "this hyperparameter.", "",
        "## Aggregated metrics", "",
        summary.to_markdown(index=False) if not summary.empty else "(no data)", "",
        "## Paradox magnitude per sub-chunk setting", "",
        "`paradox_drop` = faith_baseline − faith_v1 (positive = paradox confirmed).  ",
        "`v2_recovery` = faith_v2 − faith_v1 (positive = v2 helps).", "",
        paradox.to_markdown(index=False) if not paradox.empty else "(no data)", "",
        "A stable paradox magnitude (±0.02 faith points) across sub-chunk "
        "settings indicates the effect is structural, not tuned.",
    ]
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa"])
    parser.add_argument("--sub_chunks", nargs="+", type=int, default=[128, 256, 512])
    parser.add_argument("--model", type=str, default="mistral")
    parser.add_argument("--n_questions", type=int, default=30)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

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
            print(f"[SubChunk] unknown dataset {ds}, skipping")
            continue
        for sc in args.sub_chunks:
            key = f"{ds}__sc{sc}__{args.model}"
            if state.get(key) and not args.force:
                print(f"[SubChunk] checkpoint hit, skipping {key}")
                continue
            rows = run_tuple(ds, sc, args.model, args.n_questions, detector)
            all_rows.extend(rows)
            pd.DataFrame(rows).to_csv(
                os.path.join(OUTPUT_DIR, f"{key}_per_query.csv"), index=False
            )
            state[key] = True
            _save_checkpoint(state)

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "per_query.csv"), index=False)
    summary = aggregate(all_rows)
    summary.to_csv(os.path.join(OUTPUT_DIR, "summary.csv"), index=False)
    paradox = paradox_table(summary)
    paradox.to_csv(os.path.join(OUTPUT_DIR, "paradox_by_sub.csv"), index=False)
    write_summary_md(summary, paradox, os.path.join(OUTPUT_DIR, "summary.md"))
    print(f"[SubChunk] outputs -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
