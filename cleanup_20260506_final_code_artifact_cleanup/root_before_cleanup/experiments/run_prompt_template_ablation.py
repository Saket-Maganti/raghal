"""
run_prompt_template_ablation.py — NeurIPS Gap 2
===============================================

Tests whether the coherence paradox (faith_baseline > faith_hcpc_v1) and
the v2 recovery (faith_v2 ≥ faith_baseline) are stable across prompt
formulations — i.e. not artifacts of the single hard-coded RAG prompt in
`src/rag_pipeline.py`.

Four prompt templates are evaluated, covering the dominant families seen
in the RAG literature:

    strict   — the current production prompt (ONLY-from-context, abstain rule)
    cot      — chain-of-thought ("think step by step ... then answer")
    concise  — short-answer preference ("answer in one sentence")
    expert   — expert-role ("you are an expert <domain> researcher")

For each (dataset, template) we run three retrieval conditions — baseline,
hcpc_v1, hcpc_v2 — and report:

    paradox_drop   = faith(baseline) − faith(hcpc_v1)
    v2_recovery    = faith(hcpc_v2)  − faith(hcpc_v1)

The target finding is that `paradox_drop` stays within ±0.03 faith points
of the value reported in `results/multidataset/summary.csv` across all
four templates.  That would rule out "maybe it's just the prompt" as an
alternative explanation.

Outputs (results/prompt_ablation/):
    per_query.csv        — one row per (dataset, template, condition, question)
    summary.csv          — aggregated per (dataset, template, condition)
    paradox_by_prompt.csv — per (dataset, template): paradox_drop, v2_recovery
    summary.md           — narrative + tables for §Ablations

Run (≈ 3 h on M4 across 3 datasets × 4 templates × 3 conditions × 30 q):

    python3 experiments/run_prompt_template_ablation.py \
        --datasets squad pubmedqa hotpotqa \
        --templates strict cot concise expert \
        --model mistral --n_questions 30
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import os
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd

from langchain_core.documents import Document

from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.retrieval_metrics import compute_retrieval_quality


OUTPUT_DIR = "results/prompt_ablation"
CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, "completed_tuples.json")

CHUNK_SIZE   = 1024
TOP_K        = 3
EMBED_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"

V1_SIM = 0.50
V1_CE  = 0.00
V2_SIM = 0.45
V2_CE  = -0.20


# ── Prompt templates ─────────────────────────────────────────────────────
#
# All templates take the same two fields (context, question) so we can swap
# them in a single loop.  Each is designed to emphasise a different slice of
# the prompt-engineering design space so that if the coherence paradox is a
# prompt-specific phenomenon, at least one template should not exhibit it.

PROMPT_TEMPLATES: Dict[str, str] = {
    "strict": (
        "You are a helpful assistant that answers questions based ONLY on "
        "the provided context.\n"
        "If the answer is not in the context, say \"I cannot find this "
        "information in the provided context.\"\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer based strictly on the context above:"
    ),
    "cot": (
        "You are a careful reader.  Use the context below to answer the "
        "question.  First, think step by step about what the context says "
        "that is relevant.  Then give the final answer on a new line "
        "prefixed with \"Answer:\".\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Reasoning:"
    ),
    "concise": (
        "Answer the question using only the context.  Reply in one short "
        "sentence; do not add commentary.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n"
        "Answer:"
    ),
    "expert": (
        "You are an expert researcher.  Using only the evidence in the "
        "context, give a precise, technically-worded answer to the "
        "question.  If the evidence is insufficient, say so explicitly.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n"
        "Expert answer:"
    ),
}


def _load_checkpoint() -> Dict[str, bool]:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as fh:
            return json.load(fh)
    return {}


def _save_checkpoint(state: Dict[str, bool]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as fh:
        json.dump(state, fh, indent=2)


def _extract_answer(raw: str, template: str) -> str:
    """Post-process LLM output so NLI faithfulness compares the *answer*."""
    if template == "cot":
        # Keep everything after the final "Answer:" marker if present.
        idx = raw.rfind("Answer:")
        if idx >= 0:
            return raw[idx + len("Answer:"):].strip()
    return raw.strip()


def _generate_with_template(
    pipeline: RAGPipeline,
    question: str,
    docs: List[Document],
    template_name: str,
) -> Dict:
    """Format `docs` with the chosen template and call the LLM directly."""
    context = "\n\n---\n\n".join(d.page_content for d in docs)
    prompt = PROMPT_TEMPLATES[template_name].format(
        context=context, question=question
    )
    t0 = time.time()
    raw = pipeline.llm.invoke(prompt)
    latency = round(time.time() - t0, 2)
    answer = _extract_answer(raw, template_name)
    return {
        "answer":    answer,
        "raw":       raw,
        "context":   context,
        "latency_s": latency,
    }


def _eval_query(
    pipeline: RAGPipeline,
    qa: Dict,
    retriever,
    label: str,
    template_name: str,
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

    gen = _generate_with_template(pipeline, qa["question"], docs, template_name)
    nli = detector.detect(gen["answer"], gen["context"])
    ret_m = compute_retrieval_quality(qa["question"], docs, pipeline.embeddings)
    return {
        "question":            qa["question"],
        "ground_truth":        qa.get("ground_truth", ""),
        "answer":              gen["answer"],
        "template":            template_name,
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
    template: str,
    model: str,
    n_questions: int,
    detector: HallucinationDetector,
) -> List[Dict]:
    """Run baseline / hcpc_v1 / hcpc_v2 for one (dataset, template) pair."""
    print(f"\n{'='*72}\n[Prompt] {dataset.upper()}  template={template}\n{'='*72}")
    docs, qa = load_dataset_by_name(dataset, max_papers=30)
    if not docs or not qa:
        print(f"[Prompt] {dataset}: no data, skipping.")
        return []

    collection = f"prompt_{dataset}_{model}"
    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=TOP_K,
        model_name=model,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_prompt/{collection}",
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
                rec = _eval_query(
                    pipeline, qa_pair, retriever, label, template, detector
                )
                rec["dataset"] = dataset
                rec["model"]   = model
                rows.append(rec)
            except Exception as exc:
                print(f"[Prompt] err {dataset}/{template}/{label}: {exc}")
    return rows


def aggregate(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    grp = df.groupby(["dataset", "model", "template", "condition"])
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


def paradox_by_prompt(
    summary: pd.DataFrame, multidataset_summary_path: str,
) -> pd.DataFrame:
    if summary.empty:
        return summary
    ref_paradox = _load_reference_paradox(multidataset_summary_path)
    rows = []
    for (ds, mdl, tpl), sub in summary.groupby(
        ["dataset", "model", "template"]
    ):
        try:
            base = sub[sub["condition"] == "baseline"].iloc[0]
            v1   = sub[sub["condition"] == "hcpc_v1"].iloc[0]
            v2   = sub[sub["condition"] == "hcpc_v2"].iloc[0]
        except IndexError:
            continue
        paradox_drop = round(base["faith"] - v1["faith"], 4)
        ref = ref_paradox.get((ds, mdl))
        delta = (round(paradox_drop - ref, 4) if ref is not None else None)
        rows.append({
            "dataset":         ds,
            "model":           mdl,
            "template":        tpl,
            "faith_base":      base["faith"],
            "faith_v1":        v1["faith"],
            "faith_v2":        v2["faith"],
            "paradox_drop":    paradox_drop,
            "v2_recovery":     round(v2["faith"] - v1["faith"], 4),
            "ref_paradox_drop": ref,
            "delta_vs_ref":    delta,
            "stable":          (abs(delta) <= 0.03) if delta is not None else None,
        })
    return pd.DataFrame(rows)


def _load_reference_paradox(path: str) -> Dict[Tuple[str, str], float]:
    if not os.path.exists(path):
        return {}
    try:
        md = pd.read_csv(path)
    except Exception:
        return {}
    out: Dict[Tuple[str, str], float] = {}
    for (ds, mdl), sub in md.groupby(["dataset", "model"]):
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
        "# Prompt-template ablation (NeurIPS Gap 2)", "",
        "Four prompt templates (strict, CoT, concise, expert-role) × "
        "three retrieval conditions × three datasets, to test whether the "
        "coherence paradox and v2 recovery depend on the specific prompt "
        "used in `src/rag_pipeline.py`.", "",
        "## Aggregated metrics per (dataset, template, condition)", "",
        summary.to_markdown(index=False) if not summary.empty else "(no data)",
        "",
        "## Paradox magnitude vs reference (multidataset summary)", "",
        "`ref_paradox_drop` = paradox gap reported in "
        "`results/multidataset/summary.csv` (strict prompt).  ",
        "`delta_vs_ref` = this run's paradox_drop − ref_paradox_drop.  ",
        "`stable` = |delta_vs_ref| ≤ 0.03 (target: True across all templates).",
        "",
        paradox.to_markdown(index=False) if not paradox.empty else "(no data)",
        "",
        "If `stable == True` across all 4 × 3 = 12 cells, the paradox is "
        "not an artifact of the production prompt and survives the "
        "standard taxonomy of RAG prompt styles.",
    ]
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+",
                        default=["squad", "pubmedqa", "hotpotqa"])
    parser.add_argument("--templates", nargs="+",
                        default=list(PROMPT_TEMPLATES.keys()))
    parser.add_argument("--model", type=str, default="mistral")
    parser.add_argument("--n_questions", type=int, default=30)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--multidataset_summary", type=str,
                        default="results/multidataset/summary.csv")
    args = parser.parse_args()

    for t in args.templates:
        if t not in PROMPT_TEMPLATES:
            raise SystemExit(f"Unknown template: {t}. "
                             f"Known: {list(PROMPT_TEMPLATES)}")

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
            print(f"[Prompt] unknown dataset {ds}, skipping")
            continue
        for tpl in args.templates:
            key = f"{ds}__{tpl}__{args.model}"
            if state.get(key) and not args.force:
                print(f"[Prompt] checkpoint hit, skipping {key}")
                continue
            rows = run_tuple(ds, tpl, args.model, args.n_questions, detector)
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
    paradox = paradox_by_prompt(summary, args.multidataset_summary)
    paradox.to_csv(os.path.join(OUTPUT_DIR, "paradox_by_prompt.csv"), index=False)
    write_summary_md(summary, paradox, os.path.join(OUTPUT_DIR, "summary.md"))
    print(f"[Prompt] outputs -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
