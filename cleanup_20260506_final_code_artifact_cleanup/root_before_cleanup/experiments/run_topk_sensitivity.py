"""
experiments/run_topk_sensitivity.py — Phase 4 #4.1 (top-k ablation)
====================================================================

Runs the baseline / HCPC-v1 / HCPC-v2 / CCS-gate quartet across
top_k ∈ {2, 3, 5, 10} on SQuAD and PubMedQA with Mistral-7B (Ollama).
This is a useful missing axis: top-k is a knob
every RAG practitioner tunes, and the coherence theory predicts that
larger k *increases* relevance (more matches) but *decreases* coherence
(more disparate sources). If the paradox magnitude grows with k, the
theory is empirically supported on a hyperparameter axis reviewers
already care about.

Outputs:
    results/topk_sensitivity/per_query.csv
    results/topk_sensitivity/summary.csv
    results/topk_sensitivity/paradox_by_k.csv
    results/topk_sensitivity/summary.md
    results/topk_sensitivity/completed_tuples.json   (for resume)

Run:
    ollama serve   # in a dedicated terminal
    python3 experiments/run_topk_sensitivity.py \\
        --k 2 3 5 10 \\
        --datasets squad pubmedqa \\
        --model mistral \\
        --n_questions 30

Approximate wall clock: 4 conditions × 4 k's × 2 datasets × 30 q
× ~3 s/query = ~48 minutes per dataset, ~1.6 hr total on M4 + Ollama.
The runner is checkpoint-resumable: re-running picks up at the last
unfinished (dataset, k) pair.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

from src.dataset_loaders          import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline             import RAGPipeline
from src.hallucination_detector   import HallucinationDetector
from src.hcpc_retriever           import HCPCRetriever
from src.hcpc_v2_retriever        import HCPCv2Retriever
from src.ccs_gate_retriever       import CCSGateRetriever
from src.retrieval_metrics        import compute_retrieval_quality

OUT_DIR        = "results/topk_sensitivity"
CHECKPOINT     = os.path.join(OUT_DIR, "completed_tuples.json")
CHUNK_SIZE     = 1024
EMBED_MODEL    = "sentence-transformers/all-MiniLM-L6-v2"

V1_SIM, V1_CE = 0.50,  0.00
V2_SIM, V2_CE = 0.45, -0.20
CCS_GATE_TAU  = 0.50          # match HCPCv2's empirical operating point


def _load_checkpoint() -> Dict[str, bool]:
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as fh:
            return json.load(fh)
    return {}


def _save_checkpoint(state: Dict[str, bool]) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CHECKPOINT, "w") as fh:
        json.dump(state, fh, indent=2)


def _eval_query(
    pipeline:  RAGPipeline,
    qa:        Dict,
    retriever, label: str,
    detector:  HallucinationDetector,
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
        "gate_fired":          bool(hlog.get("gate_fired", False))
                                if isinstance(hlog, dict) else False,
        "latency_s":           gen["latency_s"],
    }


def run_tuple(
    dataset: str, k: int, model: str, n_q: int,
    detector: HallucinationDetector,
) -> List[Dict]:
    print(f"\n{'='*72}\n[Top-K] {dataset.upper()} × k={k} × {model}\n{'='*72}")
    docs, qa = load_dataset_by_name(dataset, max_papers=30)
    if not docs or not qa:
        return []

    collection = f"topk_{dataset}_k{k}_{model}"
    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=k,
        model_name=model,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_topk/{collection}",
    )
    pipeline.index_documents(docs, collection_name=collection)

    hcpc_v1 = HCPCRetriever(pipeline=pipeline, sim_threshold=V1_SIM,
                             ce_threshold=V1_CE, top_k=k)
    hcpc_v2 = HCPCv2Retriever(pipeline=pipeline, sim_threshold=V2_SIM,
                               ce_threshold=V2_CE, top_k_protected=2,
                               max_refine=2)
    # HCPCv2 reads top_k from pipeline.top_k (set above); no kwarg.
    ccs_gate = CCSGateRetriever(pipeline=pipeline,
                                 ccs_threshold=CCS_GATE_TAU, top_k=k)

    rows: List[Dict] = []
    for qa_pair in qa[:n_q]:
        for label, retr in [
            ("baseline", None),
            ("hcpc_v1",  hcpc_v1),
            ("ccs_gate", ccs_gate),
            ("hcpc_v2",  hcpc_v2),
        ]:
            try:
                rec = _eval_query(pipeline, qa_pair, retr, label, detector)
                rec["dataset"] = dataset
                rec["k"]       = k
                rec["model"]   = model
                rows.append(rec)
            except Exception as exc:
                print(f"[Top-K] err {dataset}/k{k}/{label}: {exc}")
    return rows


def aggregate(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    grp = df.groupby(["dataset", "k", "condition"])
    s = grp.agg(
        n_queries=("question", "count"),
        faith=("faithfulness_score", "mean"),
        halluc=("is_hallucination", "mean"),
        sim=("mean_retrieval_similarity", "mean"),
        refine_rate=("refined", "mean"),
        gate_rate=("gate_fired", "mean"),
        ccs=("ccs", lambda s: float(s[s >= 0].mean())
                                if (s >= 0).any() else float("nan")),
        latency=("latency_s", "mean"),
    ).reset_index()
    for c in ("faith", "halluc", "sim", "refine_rate", "gate_rate", "ccs", "latency"):
        s[c] = s[c].round(4)
    return s


def paradox_by_k(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (ds, k), sub in summary.groupby(["dataset", "k"]):
        try:
            base = sub[sub["condition"] == "baseline"].iloc[0]
            v1   = sub[sub["condition"] == "hcpc_v1"].iloc[0]
            v2   = sub[sub["condition"] == "hcpc_v2"].iloc[0]
            gate = sub[sub["condition"] == "ccs_gate"].iloc[0]
        except IndexError:
            continue
        rows.append({
            "dataset":      ds,
            "k":            int(k),
            "faith_base":   base["faith"],
            "faith_v1":     v1["faith"],
            "faith_v2":     v2["faith"],
            "faith_gate":   gate["faith"],
            "paradox":      round(base["faith"] - v1["faith"], 4),
            "v2_recovery":  round(v2["faith"] - v1["faith"], 4),
            "gate_recovery": round(gate["faith"] - v1["faith"], 4),
            "ccs_baseline": base.get("ccs", float("nan")),
        })
    return pd.DataFrame(rows)


def write_summary_md(summary: pd.DataFrame, paradox: pd.DataFrame,
                     out_path: str) -> None:
    lines = [
        "# Top-K sensitivity ablation (Phase 4 #1)", "",
        "Re-runs baseline / HCPC-v1 / CCS-gate / HCPC-v2 across k ∈ {2, 3, "
        "5, 10}. Coherence theory predicts that larger k increases "
        "relevance breadth but decreases coherence; if the paradox "
        "magnitude scales with k, the theory is empirically supported on "
        "a hyperparameter axis reviewers already care about.", "",
        "## Aggregated metrics", "",
        summary.to_markdown(index=False) if not summary.empty else "(no data)",
        "",
        "## Paradox magnitude by top-k", "",
        paradox.to_markdown(index=False) if not paradox.empty else "(no data)",
        "",
        "Target finding: paradox monotonically increases with k on at least "
        "one dataset, OR HCPC-v2 / CCS-gate recovery is stable across k.",
    ]
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k",        nargs="+", type=int, default=[2, 3, 5, 10])
    ap.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa"])
    ap.add_argument("--model",    default="mistral")
    ap.add_argument("--n_questions", type=int, default=30)
    ap.add_argument("--force",    action="store_true")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    state = _load_checkpoint()
    detector = HallucinationDetector()

    all_rows: List[Dict] = []
    prior = os.path.join(OUT_DIR, "per_query.csv")
    if os.path.exists(prior):
        try:
            all_rows.extend(pd.read_csv(prior).to_dict("records"))
        except Exception:
            pass

    for ds in args.datasets:
        if ds not in DATASET_REGISTRY:
            print(f"[Top-K] unknown dataset {ds}, skipping")
            continue
        for k in args.k:
            key = f"{ds}__k{k}"
            if state.get(key) and not args.force:
                print(f"[Top-K] checkpoint hit, skipping {key}")
                continue
            rows = run_tuple(ds, k, args.model, args.n_questions, detector)
            all_rows.extend(rows)
            pd.DataFrame(rows).to_csv(
                os.path.join(OUT_DIR, f"{key}_per_query.csv"),
                index=False,
            )
            state[key] = True
            _save_checkpoint(state)

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(OUT_DIR, "per_query.csv"), index=False)
    summary = aggregate(all_rows)
    summary.to_csv(os.path.join(OUT_DIR, "summary.csv"), index=False)
    paradox = paradox_by_k(summary)
    paradox.to_csv(os.path.join(OUT_DIR, "paradox_by_k.csv"), index=False)
    write_summary_md(summary, paradox, os.path.join(OUT_DIR, "summary.md"))
    print(f"\n[Top-K] outputs -> {OUT_DIR}/")


if __name__ == "__main__":
    main()
