"""
run_multi_retriever_ablation.py — Item #8 (added in revision)
==============================================================

Replicates the Phase-6 central contrast (baseline / hcpc_v1 / hcpc_v2)
across **four embedders that span the modern strong-retriever frontier**:

    minilm     — 22 M, the existing weak baseline
    bge-large  — 335 M, MTEB top-tier symmetric retriever
    e5-large   — 335 M, contrastive asymmetric retriever
    gte-large  — 335 M, alternative training family

This is the single piece the prior infrastructure did not address. The
review explicitly asks: "Heavy reliance on one embedding model — is this
just a property of weak embeddings? Would a stronger retriever fix
coherence?" If the refinement paradox persists across all four embedders
the coherence framing is causal; if it vanishes with the strong embedders
the framing must be tightened to "failure mode of weak retrievers".

Per (dataset, embedder, condition) cell we record:
    nli_faithfulness, hallucination_rate, mean_retrieval_similarity,
    refinement_rate, mean_ccs, n_queries

Outputs (results/multi_retriever/):
    per_query.csv               — concatenated raw rows
    summary.csv                 — aggregated per (dataset, embedder, condition)
    paradox_by_embedder.csv     — per (dataset, embedder): faith_baseline − faith_v1
                                  and v2 recovery; the headline table
    summary.md                  — human-readable digest
    completed_tuples.json       — checkpoint index for safe resume

Run:
    python3 experiments/run_multi_retriever_ablation.py \\
        --datasets squad pubmedqa \\
        --embedders minilm bge-large e5-large gte-large \\
        --n_questions 30
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.embedders import EMBEDDERS, build_embedder
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.rag_pipeline import RAGPipeline
from src.retrieval_metrics import compute_retrieval_quality

OUTPUT_DIR      = "results/multi_retriever"
CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, "completed_tuples.json")

DEFAULT_DATASETS  = ["squad", "pubmedqa"]
DEFAULT_EMBEDDERS = ["minilm", "bge-large", "e5-large", "gte-large"]

# Held fixed across the ablation — only the embedder varies.
MODEL_NAME = "mistral"
CHUNK_SIZE = 1024
TOP_K      = 3

V1_SIM_THRESHOLD = 0.50
V1_CE_THRESHOLD  = 0.00
V2_SIM_THRESHOLD = 0.45
V2_CE_THRESHOLD  = -0.20


# ── Checkpointing ────────────────────────────────────────────────────────────

def _load_checkpoint() -> Dict[str, bool]:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as fh:
            return json.load(fh)
    return {}


def _save_checkpoint(state: Dict[str, bool]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as fh:
        json.dump(state, fh, indent=2)


# ── Per-query evaluation ─────────────────────────────────────────────────────

def _eval_one_query(
    pipeline: RAGPipeline,
    qa: Dict,
    retriever,
    label: str,
    detector: HallucinationDetector,
) -> Dict:
    """Evaluate one (query, condition) cell with a fully-built pipeline."""
    if retriever is None:
        docs, _ = pipeline.retrieve_with_scores(qa["question"])
        hlog: Dict = {}
    else:
        out = retriever.retrieve(qa["question"])
        if isinstance(out, tuple):
            docs, hlog = out
        else:
            docs, hlog = out, {}

    gen   = pipeline.generate(qa["question"], docs)
    nli   = detector.detect(gen["answer"], gen["context"])
    ret_m = compute_retrieval_quality(qa["question"], docs, pipeline.embeddings)

    return {
        "question":                  qa["question"],
        "ground_truth":              qa.get("ground_truth", ""),
        "answer":                    gen["answer"],
        "condition":                 label,
        "faithfulness_score":        nli["faithfulness_score"],
        "is_hallucination":          nli["is_hallucination"],
        "mean_retrieval_similarity": ret_m.get("mean_similarity", 0.0),
        "refined":                   bool(hlog.get("refined", False)) if isinstance(hlog, dict) else False,
        "ccs":                       hlog.get("context_coherence", -1.0) if isinstance(hlog, dict) else -1.0,
        "latency_s":                 gen.get("latency_s", 0.0),
    }


# ── Per-tuple driver ─────────────────────────────────────────────────────────

def run_one_tuple(
    dataset:     str,
    embedder:    str,
    n_questions: int,
    detector:    HallucinationDetector,
) -> List[Dict]:
    """Run baseline / hcpc_v1 / hcpc_v2 on one (dataset, embedder) pair."""
    print(f"\n{'='*72}\n[MR] {dataset.upper()} × embedder={embedder}\n{'='*72}")
    docs, qa = load_dataset_by_name(dataset, max_papers=30)
    if not docs or not qa:
        print(f"[MR] {dataset}: no data, skipping")
        return []

    embedding_obj    = build_embedder(embedder)
    collection_name  = f"mr_{dataset}_{embedder}"
    persist_dir      = f"./chroma_db_mr/{collection_name}"

    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=TOP_K,
        model_name=MODEL_NAME,
        persist_dir=persist_dir,
        embeddings=embedding_obj,   # <-- the only thing we vary
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
                rec["dataset"]  = dataset
                rec["embedder"] = embedder
                rows.append(rec)
            except Exception as exc:
                print(f"[MR] error {dataset}/{embedder}/{label}: {exc}")

    return rows


# ── Aggregation ──────────────────────────────────────────────────────────────

def aggregate(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    grp = df.groupby(["dataset", "embedder", "condition"])
    summary = grp.agg(
        n_queries  = ("question",                  "count"),
        faith      = ("faithfulness_score",        "mean"),
        halluc     = ("is_hallucination",          "mean"),
        sim        = ("mean_retrieval_similarity", "mean"),
        refine_rate= ("refined",                   "mean"),
        ccs        = ("ccs", lambda s: float(s[s >= 0].mean()) if (s >= 0).any() else float("nan")),
        latency    = ("latency_s",                 "mean"),
    ).reset_index()
    for col in ["faith", "halluc", "sim", "refine_rate", "ccs", "latency"]:
        summary[col] = summary[col].round(4)
    return summary


def paradox_table(summary: pd.DataFrame) -> pd.DataFrame:
    """For each (dataset, embedder), report the paradox magnitude.

    Columns:
        faith_baseline, faith_v1, faith_v2
        paradox_drop = faith_baseline − faith_v1 (positive = paradox confirmed)
        v2_recovery  = faith_v2 − faith_v1       (positive = v2 helps)

    A reviewer can scan this single table to answer:
      "Does the paradox persist across embedders, or only on weak ones?"
    """
    if summary.empty:
        return summary
    rows = []
    for (ds, emb), sub in summary.groupby(["dataset", "embedder"]):
        try:
            base = sub[sub["condition"] == "baseline"].iloc[0]
            v1   = sub[sub["condition"] == "hcpc_v1"].iloc[0]
            v2   = sub[sub["condition"] == "hcpc_v2"].iloc[0]
        except IndexError:
            continue
        rows.append({
            "dataset":         ds,
            "embedder":        emb,
            "embedder_params": EMBEDDERS[emb].parameters,
            "faith_baseline":  base["faith"],
            "faith_v1":        v1["faith"],
            "faith_v2":        v2["faith"],
            "paradox_drop":    round(base["faith"] - v1["faith"], 4),
            "v2_recovery":     round(v2["faith"]   - v1["faith"], 4),
            "halluc_baseline": base["halluc"],
            "halluc_v1":       v1["halluc"],
            "halluc_v2":       v2["halluc"],
            "sim_baseline":    base["sim"],
            "sim_v1":          v1["sim"],
        })
    return pd.DataFrame(rows)


def write_summary_md(
    summary: pd.DataFrame,
    paradox: pd.DataFrame,
    out_path: str,
) -> None:
    lines = [
        "# Multi-retriever ablation (Item #8)",
        "",
        "Tests whether the refinement paradox is a property of context coherence",
        "or merely a property of a weak embedder. We hold the generator (Mistral-7B),",
        "the chunk size (1024), top-k (3), and the NLI scorer constant; the only",
        "varied quantity is the dense retriever embedding model.",
        "",
        "## Embedders",
        "",
    ]
    from src.embedders import display_table_md
    lines.append(display_table_md())
    lines.extend([
        "",
        "## Aggregated metrics (per dataset × embedder × condition)",
        "",
        summary.to_markdown(index=False) if not summary.empty else "(no data)",
        "",
        "## Headline: paradox magnitude per embedder",
        "",
        "`paradox_drop` = faith_baseline − faith_v1 (positive ⇒ refinement hurt)",
        "`v2_recovery`  = faith_v2 − faith_v1       (positive ⇒ coherence-preserving",
        "                                            probe restored faithfulness)",
        "",
        paradox.to_markdown(index=False) if not paradox.empty else "(no data)",
        "",
        "## Interpretation guide",
        "",
        "- If `paradox_drop` is positive across ALL embedders ⇒ coherence framing",
        "  survives the strong-retriever critique; the failure mode is general.",
        "- If `paradox_drop` shrinks to ~0 for the 335M models ⇒ the paper must",
        "  reframe as 'failure mode of weak retrievers' (still a real result, but",
        "  scope changes).",
        "- `v2_recovery` should remain positive across all embedders if HCPC-v2",
        "  is a genuine coherence-preserving intervention.",
    ])
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets",   nargs="+", default=DEFAULT_DATASETS)
    parser.add_argument("--embedders",  nargs="+", default=DEFAULT_EMBEDDERS)
    parser.add_argument("--n_questions", type=int, default=30)
    parser.add_argument("--force", action="store_true",
                        help="Re-run already-completed (dataset, embedder) tuples.")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    state = _load_checkpoint()
    detector = HallucinationDetector()

    # Resume any rows from prior partial runs so the consolidated CSV stays whole.
    all_rows: List[Dict] = []
    prior_path = os.path.join(OUTPUT_DIR, "per_query.csv")
    if os.path.exists(prior_path):
        try:
            all_rows.extend(pd.read_csv(prior_path).to_dict("records"))
        except Exception:
            pass

    for ds in args.datasets:
        if ds not in DATASET_REGISTRY:
            print(f"[MR] unknown dataset {ds}, skipping")
            continue
        for emb in args.embedders:
            if emb not in EMBEDDERS:
                print(f"[MR] unknown embedder {emb}, skipping")
                continue
            key = f"{ds}__{emb}"
            if state.get(key) and not args.force:
                print(f"[MR] checkpoint hit, skipping {key}")
                continue
            tuple_rows = run_one_tuple(ds, emb, args.n_questions, detector)
            all_rows.extend(tuple_rows)
            pd.DataFrame(tuple_rows).to_csv(
                os.path.join(OUTPUT_DIR, f"{key}_per_query.csv"), index=False
            )
            state[key] = True
            _save_checkpoint(state)

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUTPUT_DIR, "per_query.csv"), index=False)
    summary = aggregate(all_rows)
    summary.to_csv(os.path.join(OUTPUT_DIR, "summary.csv"), index=False)
    paradox = paradox_table(summary)
    paradox.to_csv(os.path.join(OUTPUT_DIR, "paradox_by_embedder.csv"), index=False)
    write_summary_md(summary, paradox, os.path.join(OUTPUT_DIR, "summary.md"))
    print(f"[MR] outputs -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
