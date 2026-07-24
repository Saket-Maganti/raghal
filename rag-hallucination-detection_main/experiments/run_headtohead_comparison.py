"""
run_headtohead_comparison.py — A4 (Self-RAG + CRAG vs HCPC)
============================================================

Replaces the §3.5–3.6 "no external comparison" caveat with an actual
head-to-head between five conditions on a shared query set:

    baseline    — fixed 1024-token chunks, standard retrieval
    hcpc_v1     — naive refinement (OR-gate, no protection)
    hcpc_v2     — selective refinement (ours)
    selfrag     — published Self-RAG-7B checkpoint (Asai et al. 2024)
    crag        — CRAG reimplementation (Yan et al. 2024) on top of our pipeline

Per (dataset, condition) we record the same metrics as the multidataset
harness, plus condition-specific diagnostics (Self-RAG reflection-token
counts, CRAG per-passage labels).

Compute notes:
    Self-RAG inference requires a GPU (T4 minimum, 14-16 GB fp16).
    HCPC + baseline + CRAG can run on M4 via Ollama.
    The runner will skip Self-RAG if the model fails to load (e.g. on M4),
    so it can be invoked once on M4 to get the other 4 conditions, then
    re-run on a GPU to fill in Self-RAG.

Outputs (results/headtohead/):
    per_query.csv         — one row per (dataset, condition, query)
    summary.csv           — aggregated faithfulness / hallucination by condition
    diagnostics.jsonl     — per-query Self-RAG / CRAG decision dumps
    summary.md            — markdown digest for paper §Results

Run:
    python3 experiments/run_headtohead_comparison.py \
        --datasets squad pubmedqa hotpotqa \
        --n_questions 30 \
        --selfrag_device cuda
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
from typing import Dict, List

import pandas as pd

from src.dataset_loaders import DATASET_REGISTRY, load_dataset_by_name
from src.rag_pipeline import RAGPipeline
from src.hallucination_detector import HallucinationDetector
from src.hcpc_retriever import HCPCRetriever
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.crag_retriever import CRAGRetriever
from src.retrieval_metrics import compute_retrieval_quality

OUTPUT_DIR = "results/headtohead"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE  = 1024
TOP_K       = 3


def _maybe_load_selfrag(device: str | None,
                        load_in_8bit: bool = False,
                        load_in_4bit: bool = False):
    """Load Self-RAG with optional bitsandbytes quantization.

    Use `--selfrag_8bit` on a single T4 to avoid the OOM we hit on Kaggle
    when running Self-RAG alongside Ollama + embeddings.  `--selfrag_4bit`
    is the last resort if you also need another 7B model co-resident.
    """
    try:
        from src.selfrag_wrapper import SelfRAGGenerator
        gen = SelfRAGGenerator(
            device=device,
            load_in_8bit=load_in_8bit,
            load_in_4bit=load_in_4bit,
        )
        gen.load()
        return gen
    except Exception as exc:
        print(f"[H2H] Self-RAG unavailable: {exc}")
        return None


def _evaluate_condition(
    label: str,
    pipeline: RAGPipeline,
    retriever,
    qa_pair: Dict,
    detector: HallucinationDetector,
    selfrag=None,
    diag_fh=None,
) -> Dict:
    if label == "selfrag":
        if selfrag is None:
            return {"condition": label, "skipped": True}
        # Self-RAG needs retrieved passages too; we feed it the baseline retrieval.
        docs, _ = pipeline.retrieve_with_scores(qa_pair["question"])
        gen = selfrag.generate(qa_pair["question"], docs)
        diag = {
            "condition":     label,
            "question":      qa_pair["question"],
            "selfrag_parsed": gen.get("selfrag_parsed", {}),
        }
    elif label == "baseline":
        docs, _ = pipeline.retrieve_with_scores(qa_pair["question"])
        gen = pipeline.generate(qa_pair["question"], docs)
        diag = {"condition": label, "question": qa_pair["question"]}
    else:
        out = retriever.retrieve(qa_pair["question"])
        if isinstance(out, tuple):
            docs, hlog = out
        else:
            docs, hlog = out, {}
        gen = pipeline.generate(qa_pair["question"], docs)
        diag = {
            "condition": label,
            "question":  qa_pair["question"],
            "retriever_log": hlog,
        }

    if diag_fh is not None:
        diag_fh.write(json.dumps(diag, default=str) + "\n")

    nli = detector.detect(gen["answer"], gen["context"])
    ret_m = compute_retrieval_quality(
        qa_pair["question"],
        gen.get("retrieved_docs", []) or [],
        pipeline.embeddings,
    )
    return {
        "condition":          label,
        "question":           qa_pair["question"],
        "ground_truth":       qa_pair.get("ground_truth", ""),
        "answer":             gen["answer"],
        "faithfulness_score": nli["faithfulness_score"],
        "is_hallucination":   nli["is_hallucination"],
        "mean_retrieval_similarity": ret_m.get("mean_similarity", 0.0),
        "latency_s":          gen.get("latency_s", 0.0),
    }


def run_dataset(
    dataset: str,
    n_questions: int,
    detector: HallucinationDetector,
    selfrag,
    diag_fh,
) -> List[Dict]:
    docs, qa = load_dataset_by_name(dataset, max_papers=30)
    if not docs or not qa:
        print(f"[H2H] {dataset}: no data, skipping")
        return []

    collection_name = f"h2h_{dataset}"
    pipeline = RAGPipeline(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=int(CHUNK_SIZE * 0.1),
        top_k=TOP_K,
        embed_model=EMBED_MODEL,
        persist_dir=f"./chroma_db_h2h/{collection_name}",
    )
    pipeline.index_documents(docs, collection_name=collection_name)

    hcpc_v1 = HCPCRetriever(pipeline=pipeline, sim_threshold=0.50, ce_threshold=0.0,
                             sub_chunk_size=256, sub_chunk_overlap=32, top_k=TOP_K)
    hcpc_v2 = HCPCv2Retriever(pipeline=pipeline, sim_threshold=0.45,
                              ce_threshold=-0.20, top_k_protected=2, max_refine=2,
                              sub_chunk_size=256, sub_chunk_overlap=32)
    crag    = CRAGRetriever(pipeline=pipeline)

    rows: List[Dict] = []
    for qa_pair in qa[:n_questions]:
        for label, ret in [
            ("baseline", None),
            ("hcpc_v1",  hcpc_v1),
            ("hcpc_v2",  hcpc_v2),
            ("crag",     crag),
            ("selfrag",  None),
        ]:
            try:
                rec = _evaluate_condition(
                    label, pipeline, ret, qa_pair, detector,
                    selfrag=selfrag, diag_fh=diag_fh,
                )
                rec["dataset"] = dataset
                rows.append(rec)
            except Exception as exc:
                print(f"[H2H] error {dataset}/{label}: {exc}")
    return rows


def aggregate(rows: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame([r for r in rows if not r.get("skipped")])
    if df.empty:
        return df
    return df.groupby(["dataset", "condition"]).agg(
        n=("question", "count"),
        faith=("faithfulness_score", "mean"),
        halluc=("is_hallucination", "mean"),
        sim=("mean_retrieval_similarity", "mean"),
        latency=("latency_s", "mean"),
    ).round(4).reset_index()


def write_summary_md(summary: pd.DataFrame, out_path: str) -> None:
    lines = ["# Head-to-head: HCPC vs Self-RAG vs CRAG", "", "## Aggregated metrics", ""]
    lines.append(summary.to_markdown(index=False) if not summary.empty else "(no data)")
    lines.append("")
    lines.append(
        "Comparison conventions:\n"
        "- `baseline` and `hcpc_*` and `crag` use Ollama-served Mistral-7B.\n"
        "- `selfrag` uses the published `selfrag/selfrag_llama2_7b` checkpoint.\n"
        "- All conditions use the same retrieval corpus and top-k=3.\n"
        "- CRAG is a reimplementation; web search is disabled by default."
    )
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["squad", "pubmedqa", "hotpotqa"])
    parser.add_argument("--n_questions", type=int, default=30)
    parser.add_argument("--selfrag_device", default=None)
    parser.add_argument("--skip_selfrag", action="store_true")
    parser.add_argument("--selfrag_8bit", action="store_true",
                        help="load Self-RAG with bitsandbytes 8-bit quant "
                             "(required on a single T4 alongside Ollama)")
    parser.add_argument("--selfrag_4bit", action="store_true",
                        help="load Self-RAG with bitsandbytes 4-bit NF4 quant "
                             "(last resort; lowest peak VRAM)")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    detector = HallucinationDetector()
    selfrag = None if args.skip_selfrag else _maybe_load_selfrag(
        args.selfrag_device,
        load_in_8bit=args.selfrag_8bit,
        load_in_4bit=args.selfrag_4bit,
    )

    diag_path = os.path.join(OUTPUT_DIR, "diagnostics.jsonl")
    rows: List[Dict] = []
    with open(diag_path, "w") as diag_fh:
        for ds in args.datasets:
            if ds not in DATASET_REGISTRY:
                print(f"[H2H] unknown dataset {ds}, skipping")
                continue
            rows.extend(run_dataset(ds, args.n_questions, detector, selfrag, diag_fh))

    pd.DataFrame(rows).to_csv(os.path.join(OUTPUT_DIR, "per_query.csv"), index=False)
    summary = aggregate(rows)
    summary.to_csv(os.path.join(OUTPUT_DIR, "summary.csv"), index=False)
    write_summary_md(summary, os.path.join(OUTPUT_DIR, "summary.md"))
    print(f"[H2H] outputs -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
