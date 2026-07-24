"""
run_longform_eval.py — Phase 2 Item 3 (long-form generation eval)
=================================================================

Re-runs the baseline / HCPC-v1 / HCPC-v2 comparison on long-form QA
datasets (QASPER, MS-MARCO) and reports ROUGE-L, per-claim NLI, and the
coherence paradox gap on multi-sentence outputs.

Reviewer question answered: *"Does the coherence paradox generalize beyond
short-answer QA?"*  If `paradox_drop` (base faith − v1 faith) and
`v2_recovery` (v2 faith − v1 faith) hold on these long-form datasets, the
paper's claim is no longer confined to SQuAD-style extractive QA.

For each query we compute:

    span_faithfulness       — classic one-span NLI (comparable to short-form)
    mean_claim_faith        — mean per-sentence NLI entailment
    min_claim_faith         — worst-case claim
    unsupported_claim_rate  — fraction of claims below 0.5 entailment
    rouge_l_f1              — vs gold free-form answer
    answer_tokens           — length statistic

Outputs (results/longform/):
    per_query.csv               — one row per (dataset, condition, question)
    summary.csv                 — aggregated per (dataset, condition)
    paradox_longform.csv        — paradox_drop, v2_recovery per dataset
                                   on both span_faith and mean_claim_faith
    summary.md                  — narrative + tables for §Results / §Ablations

Run (≈ 2.5 h on M4 / ~1.5 h on Kaggle T4 for qasper + msmarco, 20 q each):

    python3 experiments/run_longform_eval.py \
        --datasets qasper msmarco --model mistral --n_questions 20

Kaggle recipe:
    !python3 experiments/run_longform_eval.py \
        --datasets qasper msmarco --model mistral --n_questions 20 && \
     zip -r /kaggle/working/longform.zip results/longform
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import os
from typing import Dict, List, Optional

import pandas as pd

from langchain_core.documents import Document

from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.longform_metrics import score_longform
from src.retrieval_metrics import compute_retrieval_quality


OUTPUT_DIR = "results/longform"
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
    gold = qa.get("ground_truth", "") or ""
    m = score_longform(
        answer=gen["answer"], context=gen["context"],
        gold_answer=gold, detector=detector,
    )
    ret_m = compute_retrieval_quality(qa["question"], docs, pipeline.embeddings)

    return {
        "question":                 qa["question"],
        "ground_truth":             gold,
        "answer":                   gen["answer"],
        "condition":                label,
        # short-form comparability
        "span_faithfulness":        m["span_faithfulness"],
        # long-form metrics
        "mean_claim_faith":         m["mean_claim_faith"],
        "min_claim_faith":          m["min_claim_faith"],
        "unsupported_claim_rate":   m["unsupported_claim_rate"],
        "rouge_l_f1":               m["rouge_l_f1"],
        "answer_tokens":            m["answer_tokens"],
        "gold_tokens":              m["gold_tokens"],
        "n_claims":                 m["n_claims"],
        "is_hallucination_long":    m["is_hallucination_long"],
        # retrieval quality
        "mean_retrieval_similarity": ret_m.get("mean_similarity", 0.0),
        # HCPC log
        "refined":                  bool(hlog.get("refined", False))
                                      if isinstance(hlog, dict) else False,
        "ccs":                      hlog.get("context_coherence", -1.0)
                                      if isinstance(hlog, dict) else -1.0,
        "latency_s":                gen["latency_s"],
    }


def run_one(
    dataset: str,
    model: str,
    n_questions: int,
    detector: HallucinationDetector,
) -> List[Dict]:
    print(f"\n{'='*72}\n[LongForm] {dataset.upper()} × {model}\n{'='*72}")
    docs, qa = load_dataset_by_name(dataset, max_papers=30)
    if not docs or not qa:
        print(f"[LongForm] {dataset}: no data, skipping.")
        return []

    collection = f"longform_{dataset}_{model}"
    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=TOP_K,
        model_name=model,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_longform/{collection}",
    )
    pipeline.index_documents(docs, collection_name=collection)

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
                rec["model"]   = model
                rows.append(rec)
            except Exception as exc:
                print(f"[LongForm] err {dataset}/{label}: {exc}")
    return rows


def aggregate(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    grp = df.groupby(["dataset", "model", "condition"])
    summary = grp.agg(
        n_queries=("question", "count"),
        span_faith=("span_faithfulness", "mean"),
        claim_faith=("mean_claim_faith", "mean"),
        min_claim_faith=("min_claim_faith", "mean"),
        unsupported_rate=("unsupported_claim_rate", "mean"),
        rouge_l=("rouge_l_f1", "mean"),
        mean_answer_tokens=("answer_tokens", "mean"),
        mean_claims=("n_claims", "mean"),
        halluc_long=("is_hallucination_long", "mean"),
        refine_rate=("refined", "mean"),
        ccs=("ccs", lambda s: float(s[s >= 0].mean())
                              if (s >= 0).any() else float("nan")),
        latency=("latency_s", "mean"),
    ).reset_index()
    for c in (
        "span_faith", "claim_faith", "min_claim_faith",
        "unsupported_rate", "rouge_l", "mean_answer_tokens",
        "mean_claims", "halluc_long", "refine_rate", "ccs", "latency",
    ):
        summary[c] = summary[c].round(4)
    return summary


def paradox_table(summary: pd.DataFrame) -> pd.DataFrame:
    """Paradox magnitude on both aggregations (span + claim-level)."""
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
            "dataset":                   ds,
            "model":                     mdl,
            # span-level (comparable to short-form tables)
            "span_faith_base":           base["span_faith"],
            "span_faith_v1":             v1["span_faith"],
            "span_faith_v2":             v2["span_faith"],
            "span_paradox_drop":         round(base["span_faith"]
                                                - v1["span_faith"], 4),
            "span_v2_recovery":          round(v2["span_faith"]
                                                - v1["span_faith"], 4),
            # claim-level (the long-form metric)
            "claim_faith_base":          base["claim_faith"],
            "claim_faith_v1":            v1["claim_faith"],
            "claim_faith_v2":            v2["claim_faith"],
            "claim_paradox_drop":        round(base["claim_faith"]
                                                - v1["claim_faith"], 4),
            "claim_v2_recovery":         round(v2["claim_faith"]
                                                - v1["claim_faith"], 4),
            # answer quality
            "rouge_l_base":              base["rouge_l"],
            "rouge_l_v1":                v1["rouge_l"],
            "rouge_l_v2":                v2["rouge_l"],
            "unsupported_rate_base":     base["unsupported_rate"],
            "unsupported_rate_v1":       v1["unsupported_rate"],
            "unsupported_rate_v2":       v2["unsupported_rate"],
        })
    return pd.DataFrame(rows)


def write_summary_md(
    summary: pd.DataFrame, paradox: pd.DataFrame, out_path: str,
) -> None:
    lines = [
        "# Long-form generation eval (Phase 2 Item 3)", "",
        "Answers the reviewer question: *does the coherence paradox "
        "generalize beyond short-answer QA to long-form generation?*  "
        "Runs on QASPER (scientific long-form QA) and MS-MARCO v2.1 "
        "(open-domain long-form), measuring both the single-span NLI "
        "faithfulness used in the main tables and per-claim NLI "
        "faithfulness designed for multi-sentence outputs.", "",
        "## Aggregated metrics per (dataset, condition)", "",
        summary.to_markdown(index=False) if not summary.empty else "(no data)",
        "",
        "## Paradox magnitude on long-form outputs", "",
        "`span_*` columns reuse the single-span NLI metric for "
        "backward comparability.  `claim_*` columns use the per-sentence "
        "aggregation.  A paradox that appears on *both* is stronger "
        "evidence than one that appears only on the coarse span metric.",
        "",
        paradox.to_markdown(index=False) if not paradox.empty else "(no data)",
        "",
        "## Interpretation targets", "",
        "1. `claim_paradox_drop > 0` on at least one dataset → paradox "
        "generalizes to long-form.  ",
        "2. `claim_v2_recovery ≥ 0` on every dataset → v2 remains a net "
        "win under the claim-level aggregation.  ",
        "3. `rouge_l_v2 ≥ rouge_l_baseline` → v2 does not sacrifice "
        "answer-quality vs the gold reference while improving "
        "faithfulness.",
    ]
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["qasper", "msmarco"])
    parser.add_argument("--model", type=str, default="mistral")
    parser.add_argument("--n_questions", type=int, default=20)
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
            print(f"[LongForm] unknown dataset {ds}, skipping")
            continue
        key = f"{ds}__{args.model}"
        if state.get(key) and not args.force:
            print(f"[LongForm] checkpoint hit, skipping {key}")
            continue
        rows = run_one(ds, args.model, args.n_questions, detector)
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
    paradox.to_csv(os.path.join(OUTPUT_DIR, "paradox_longform.csv"), index=False)
    write_summary_md(summary, paradox, os.path.join(OUTPUT_DIR, "summary.md"))
    print(f"[LongForm] outputs -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
