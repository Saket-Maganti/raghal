"""
experiments/run_raptor_ablation.py — Phase 2 Item 1
====================================================

Head-to-head comparison of RAPTOR (tree-organized retrieval) against our
HCPC-v1/v2 retrievers, on the same (dataset, model) grid used in the main
results.  This closes the "why didn't you compare to RAPTOR?" reviewer gap.

Conditions
----------
    baseline   — dense top-k over 1024-tok chunks (same as multidataset)
    hcpc_v1    — our Table 2 result
    hcpc_v2    — our Table 2 result
    raptor     — 2-level RAPTOR (leaves + 1 summary layer), mixed retrieval

Datasets / models
-----------------
Defaults: squad + pubmedqa + hotpotqa × mistral.  The grid is intentionally
narrower than the full multidataset sweep because RAPTOR's tree build cost
is O(n_clusters) LLM calls per corpus — a 3-dataset × 3-model sweep would
add ~45 min of summary generation on top of retrieval.  Users who want the
full grid can pass `--datasets ... --model ...` explicitly.

Outputs (results/raptor/)
-------------------------
    per_query.csv        — one row per (ds, cond, question)
    summary.csv          — per (ds, cond): mean faith, halluc rate, etc.
    raptor_vs_hcpc.csv   — deltas: (raptor - hcpc_v1), (raptor - hcpc_v2)
    summary.md           — markdown report for §Results

Budget
------
≈ 30 questions × 4 conditions × 3 datasets × 1 model = 360 generations
plus 6 summary LLM calls per dataset (n_clusters default = 6) → ~90 min
on the M4.  Usable as an overnight addition to the main runs.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import os
from typing import Any, Dict, List

import pandas as pd

from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.raptor_retriever import RAPTORRetriever
from src.retrieval_metrics import compute_retrieval_quality

OUT_DIR = "results/raptor"

V1_SIM, V1_CE = 0.50, 0.00
V2_SIM, V2_CE = 0.45, -0.20
CHUNK_SIZE, TOP_K = 1024, 3


def _eval_query(pipeline, qa, retriever, label, detector) -> Dict:
    if retriever is None:
        docs, _sims = pipeline.retrieve_with_scores(qa["question"])
        hlog: Dict[str, Any] = {}
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
        "question":           qa["question"],
        "ground_truth":       qa.get("ground_truth", ""),
        "answer":             gen["answer"],
        "condition":          label,
        "faithfulness_score": nli["faithfulness_score"],
        "is_hallucination":   nli["is_hallucination"],
        "mean_retrieval_similarity": ret_m.get("mean_similarity", 0.0),
        "refined":            bool(hlog.get("refined", False)) if isinstance(hlog, dict) else False,
        "ccs":                hlog.get("context_coherence", -1.0) if isinstance(hlog, dict) else -1.0,
        # RAPTOR-specific diagnostics (safe no-ops elsewhere):
        "n_summaries_returned": int(hlog.get("n_summaries_returned", 0))
                                if isinstance(hlog, dict) else 0,
        "n_leaves_returned":    int(hlog.get("n_leaves_returned", 0))
                                if isinstance(hlog, dict) else 0,
    }


def run_one_dataset(ds: str, model: str, n_q: int,
                    detector: HallucinationDetector) -> List[Dict]:
    print(f"\n{'='*72}\n[RAPTOR-ABL] {ds.upper()} × {model}\n{'='*72}")
    docs, qa = load_dataset_by_name(ds, max_papers=30)
    if not docs or not qa:
        print(f"[RAPTOR-ABL] {ds}: empty load, skipping.")
        return []

    coll = f"raptor_{ds}_{model}"
    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=TOP_K,
        model_name=model,
        persist_dir=f"./chroma_db_raptor/{coll}",
    )
    pipeline.index_documents(docs, collection_name=coll)

    hcpc_v1 = HCPCRetriever(pipeline=pipeline, sim_threshold=V1_SIM,
                            ce_threshold=V1_CE,
                            sub_chunk_size=256, sub_chunk_overlap=32,
                            top_k=TOP_K)
    hcpc_v2 = HCPCv2Retriever(pipeline=pipeline, sim_threshold=V2_SIM,
                              ce_threshold=V2_CE, top_k_protected=2,
                              max_refine=2, sub_chunk_size=256,
                              sub_chunk_overlap=32)
    raptor  = RAPTORRetriever(pipeline=pipeline, docs=docs,
                              n_clusters=6, top_k=TOP_K)

    rows: List[Dict] = []
    for qa_pair in qa[:n_q]:
        for label, retr in [
            ("baseline", None),
            ("hcpc_v1",  hcpc_v1),
            ("hcpc_v2",  hcpc_v2),
            ("raptor",   raptor),
        ]:
            try:
                rec = _eval_query(pipeline, qa_pair, retr, label, detector)
                rec["dataset"] = ds
                rec["model"]   = model
                rows.append(rec)
            except Exception as exc:
                print(f"[RAPTOR-ABL] err {ds}/{label}: {exc}")
    return rows


def aggregate(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    g = df.groupby(["dataset", "model", "condition"], as_index=False).agg(
        n_queries=("question", "count"),
        faith=("faithfulness_score", "mean"),
        halluc=("is_hallucination", "mean"),
        sim=("mean_retrieval_similarity", "mean"),
        refine_rate=("refined", "mean"),
        mean_summaries=("n_summaries_returned", "mean"),
        mean_leaves=("n_leaves_returned", "mean"),
    )
    for c in ("faith", "halluc", "sim", "refine_rate",
              "mean_summaries", "mean_leaves"):
        g[c] = g[c].round(4)
    return g


def raptor_vs_hcpc(summary: pd.DataFrame) -> pd.DataFrame:
    """For each (dataset, model), report RAPTOR faith / halluc vs v1 + v2."""
    if summary.empty:
        return summary
    out = []
    for (ds, mdl), sub in summary.groupby(["dataset", "model"]):
        try:
            b  = sub[sub["condition"] == "baseline"].iloc[0]
            v1 = sub[sub["condition"] == "hcpc_v1"].iloc[0]
            v2 = sub[sub["condition"] == "hcpc_v2"].iloc[0]
            r  = sub[sub["condition"] == "raptor"].iloc[0]
        except IndexError:
            continue
        out.append({
            "dataset": ds, "model": mdl,
            "faith_baseline": b["faith"], "faith_v1": v1["faith"],
            "faith_v2": v2["faith"],      "faith_raptor": r["faith"],
            "halluc_baseline": b["halluc"], "halluc_v1": v1["halluc"],
            "halluc_v2": v2["halluc"],      "halluc_raptor": r["halluc"],
            "raptor_vs_v1_faith":  round(r["faith"]  - v1["faith"], 4),
            "raptor_vs_v2_faith":  round(r["faith"]  - v2["faith"], 4),
            "raptor_vs_v1_halluc": round(r["halluc"] - v1["halluc"], 4),
            "raptor_vs_v2_halluc": round(r["halluc"] - v2["halluc"], 4),
        })
    return pd.DataFrame(out)


def write_markdown(summary: pd.DataFrame, vs: pd.DataFrame, path: str) -> None:
    lines = [
        "# RAPTOR head-to-head (Phase 2 Item 1)",
        "",
        "Compared conditions: `baseline`, `hcpc_v1`, `hcpc_v2`, `raptor`.",
        "RAPTOR config: 2-level tree, n_clusters=6, mix_ratio=0.5 "
        "(≥1 summary slot, rest leaves).",
        "",
        "## Aggregated metrics",
        "",
        summary.to_markdown(index=False) if not summary.empty else "(no data)",
        "",
        "## RAPTOR vs HCPC deltas",
        "",
        "Positive `raptor_vs_v*_faith` = RAPTOR wins on faithfulness.",
        "Negative `raptor_vs_v*_halluc` = RAPTOR has fewer hallucinations.",
        "",
        vs.to_markdown(index=False) if not vs.empty else "(no data)",
        "",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datasets", nargs="+",
                    default=["squad", "pubmedqa", "hotpotqa"])
    ap.add_argument("--model", default="mistral")
    ap.add_argument("--n_questions", type=int, default=30)
    ap.add_argument("--out_dir", default=OUT_DIR)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    detector = HallucinationDetector()

    all_rows: List[Dict] = []
    for ds in args.datasets:
        if ds not in DATASET_REGISTRY:
            print(f"[RAPTOR-ABL] unknown dataset {ds}, skipping")
            continue
        rows = run_one_dataset(ds, args.model, args.n_questions, detector)
        all_rows.extend(rows)
        if rows:
            pd.DataFrame(rows).to_csv(
                os.path.join(args.out_dir, f"{ds}_{args.model}_per_query.csv"),
                index=False,
            )

    if not all_rows:
        raise SystemExit("[RAPTOR-ABL] collected no rows.")

    df = pd.DataFrame(all_rows)
    df.to_csv(os.path.join(args.out_dir, "per_query.csv"), index=False)
    summary = aggregate(all_rows)
    summary.to_csv(os.path.join(args.out_dir, "summary.csv"), index=False)
    vs = raptor_vs_hcpc(summary)
    vs.to_csv(os.path.join(args.out_dir, "raptor_vs_hcpc.csv"), index=False)
    write_markdown(summary, vs, os.path.join(args.out_dir, "summary.md"))
    print(f"[RAPTOR-ABL] outputs -> {args.out_dir}/")


if __name__ == "__main__":
    main()
