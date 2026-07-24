"""
Fix 13: stronger-retriever / embedding-model sanity check.

This script provides two compact, traceable checks without paid APIs:

1. Re-encode the Fix 1 matched HIGH/LOW contexts with MiniLM plus stronger
   cached embedders (default: BGE-large and E5-large). This tests whether the
   matched-CCS diagnostic depends on the original MiniLM geometry. It reuses
   existing generations and labels; it does not rerun generation.
2. Import the already completed multi-retriever generation ablation
   (`results/multi_retriever/paradox_by_embedder.csv`) as the scaled-paradox
   sanity cell. That artifact varies MiniLM/BGE/E5/GTE retrievers with the
   generator and scorer held fixed.

Primary command:

    python3 experiments/fix_13_retriever_sanity.py

Outputs:
    data/revision/fix_13/matched_context_reencoded.csv
    data/revision/fix_13/scaled_paradox_input_copy.csv
    results/revision/fix_13/retriever_sanity_summary.csv
    results/revision/fix_13/retriever_sanity_report.md
    source_tables/retriever_sanity_summary.csv
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd

from experiments.revision_utils import ensure_dirs
from src.embedders import EMBEDDERS


OUT_DATA = Path("data/revision/fix_13")
OUT_RESULTS = Path("results/revision/fix_13")
OUT_SOURCE = Path("source_tables")
DEFAULT_EMBEDDERS = ["minilm", "bge-large", "e5-large"]


def parse_passages(value: Any) -> List[str]:
    try:
        parsed = json.loads(str(value))
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except Exception:
        pass
    return []


def l2_normalize(x: np.ndarray) -> np.ndarray:
    return x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)


def ccs_from_embeddings(mat: np.ndarray) -> float:
    if len(mat) < 2:
        return 1.0
    sims = mat @ mat.T
    upper = sims[np.triu_indices(len(mat), k=1)]
    return float(upper.mean() - upper.std())


def build_context_rows(
    per_query_path: Path,
    matched_path: Path,
    span_rows_path: Path,
) -> pd.DataFrame:
    per_query = pd.read_csv(per_query_path)
    matched = pd.read_csv(matched_path)
    rows: List[Dict[str, Any]] = []
    for _, row in matched.iterrows():
        for set_type, passage_col in [
            ("high_ccs", "high_passages_json"),
            ("low_ccs", "low_passages_json"),
        ]:
            rows.append(
                {
                    "pair_id": row["pair_id"],
                    "set_type": set_type,
                    "passages": parse_passages(row[passage_col]),
                }
            )
    contexts = pd.DataFrame(rows)
    df = per_query.merge(contexts, on=["pair_id", "set_type"], how="left")
    if span_rows_path.exists():
        span = pd.read_csv(span_rows_path, usecols=["pair_id", "set_type", "answer_span_present"])
        df = df.merge(span, on=["pair_id", "set_type"], how="left")
    else:
        df["answer_span_present"] = np.nan
    df["is_hallucination"] = df["is_hallucination"].astype(str).str.lower().isin(["true", "1", "yes"])
    return df


def encode_texts(model, texts: Sequence[str], prefix: str, batch_size: int) -> Dict[str, np.ndarray]:
    unique = list(dict.fromkeys(str(t) for t in texts))
    prefixed = [prefix + text if prefix else text for text in unique]
    vecs = model.encode(
        prefixed,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    vecs = l2_normalize(np.asarray(vecs, dtype=float))
    return {text: vec for text, vec in zip(unique, vecs)}


def reencode_contexts(df: pd.DataFrame, embedders: Sequence[str], batch_size: int) -> pd.DataFrame:
    from sentence_transformers import SentenceTransformer
    import torch

    if torch.cuda.is_available():
        device = "cuda"
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    all_questions = df["question"].fillna("").astype(str).tolist()
    all_passages: List[str] = []
    for passages in df["passages"]:
        all_passages.extend(passages or [])

    rows: List[Dict[str, Any]] = []
    for emb in embedders:
        spec = EMBEDDERS[emb]
        print(f"[Fix13] loading {spec.hf_name} on {device}", flush=True)
        model = SentenceTransformer(spec.hf_name, device=device)
        q_vec = encode_texts(model, all_questions, spec.query_prefix, batch_size)
        p_vec = encode_texts(model, all_passages, spec.passage_prefix, batch_size)
        for _, row in df.iterrows():
            passages = row["passages"] or []
            if not passages:
                continue
            mat = np.vstack([p_vec[p] for p in passages])
            q = q_vec[str(row["question"])]
            sims = mat @ q
            rows.append(
                {
                    "embedder": emb,
                    "pair_id": row["pair_id"],
                    "set_type": row["set_type"],
                    "question": row["question"],
                    "ground_truth": row["ground_truth"],
                    "faithfulness_score": float(row["faithfulness_score"]),
                    "is_hallucination": bool(row["is_hallucination"]),
                    "answer_span_present": row.get("answer_span_present", np.nan),
                    "reencoded_mean_query_sim": float(np.mean(sims)),
                    "reencoded_ccs": ccs_from_embeddings(mat),
                    "n_passages": len(passages),
                }
            )
        del model
    return pd.DataFrame(rows)


def summarize_reencoded(reencoded: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for emb, sub in reencoded.groupby("embedder"):
        wide = sub.pivot(index="pair_id", columns="set_type", values=["reencoded_ccs", "reencoded_mean_query_sim"])
        ccs_delta = wide["reencoded_ccs"]["high_ccs"] - wide["reencoded_ccs"]["low_ccs"]
        sim_gap = (wide["reencoded_mean_query_sim"]["high_ccs"] - wide["reencoded_mean_query_sim"]["low_ccs"]).abs()
        high = sub[sub["set_type"].eq("high_ccs")]
        low = sub[sub["set_type"].eq("low_ccs")]
        rows.append(
            {
                "panel": "matched_fixed_context_reencoded",
                "dataset": "squad",
                "embedder": emb,
                "n_pairs": int(len(wide)),
                "mean_ccs_high": round(float(high["reencoded_ccs"].mean()), 6),
                "mean_ccs_low": round(float(low["reencoded_ccs"].mean()), 6),
                "mean_ccs_delta_high_minus_low": round(float(ccs_delta.mean()), 6),
                "share_delta_positive": round(float((ccs_delta > 0).mean()), 6),
                "mean_abs_similarity_gap": round(float(sim_gap.mean()), 6),
                "faith_high_minus_low_existing_generation": round(
                    float(high["faithfulness_score"].mean() - low["faithfulness_score"].mean()), 6
                ),
                "halluc_high": round(float(high["is_hallucination"].mean()), 6),
                "halluc_low": round(float(low["is_hallucination"].mean()), 6),
                "span_high": round(float(pd.to_numeric(high["answer_span_present"]).mean()), 6),
                "span_low": round(float(pd.to_numeric(low["answer_span_present"]).mean()), 6),
                "paradox_drop": "",
                "v2_recovery": "",
                "source": "data/revision/fix_01 + re-encoded passages",
            }
        )
    return pd.DataFrame(rows)


def summarize_scaled(paradox_path: Path) -> pd.DataFrame:
    if not paradox_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(paradox_path)
    rows: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "panel": "scaled_paradox_generation",
                "dataset": row["dataset"],
                "embedder": row["embedder"],
                "n_pairs": "",
                "mean_ccs_high": "",
                "mean_ccs_low": "",
                "mean_ccs_delta_high_minus_low": "",
                "share_delta_positive": "",
                "mean_abs_similarity_gap": "",
                "faith_high_minus_low_existing_generation": "",
                "halluc_high": "",
                "halluc_low": "",
                "span_high": "",
                "span_low": "",
                "paradox_drop": row["paradox_drop"],
                "v2_recovery": row["v2_recovery"],
                "source": str(paradox_path),
            }
        )
    return pd.DataFrame(rows)


def write_report(summary: pd.DataFrame, out_path: Path) -> None:
    matched = summary[summary["panel"].eq("matched_fixed_context_reencoded")]
    scaled = summary[summary["panel"].eq("scaled_paradox_generation")]
    lines = [
        "# Fix 13 - stronger retriever sanity check",
        "",
        "This check is deliberately split: the matched-CCS rows are fixed-context re-encodings, while the scaled-paradox rows are imported from the completed multi-retriever generation ablation.",
        "No paid APIs are used.",
        "",
        "## Matched fixed-context re-encoding",
        "",
        matched.to_markdown(index=False) if not matched.empty else "(not run)",
        "",
        "## Scaled paradox generation cells",
        "",
        scaled.to_markdown(index=False) if not scaled.empty else "(not available)",
        "",
        "## Compact interpretation",
        "",
        "Stronger embeddings change the retrieval surface; they do not remove the need to report context structure, retriever identity, and scorer choice.",
        "The fixed-context portion should not be read as a fresh generation experiment.",
        "",
    ]
    out_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per_query", default="data/revision/fix_01/per_query.csv")
    parser.add_argument("--matched_pairs", default="data/revision/fix_01/matched_pairs.csv")
    parser.add_argument("--span_rows", default="data/revision/fix_12/span_control_rows.csv")
    parser.add_argument("--paradox_by_embedder", default="results/multi_retriever/paradox_by_embedder.csv")
    parser.add_argument("--embedders", nargs="+", default=DEFAULT_EMBEDDERS, choices=list(EMBEDDERS))
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--skip_reencode", action="store_true")
    args = parser.parse_args()

    ensure_dirs(OUT_DATA, OUT_RESULTS, OUT_SOURCE)
    source = build_context_rows(Path(args.per_query), Path(args.matched_pairs), Path(args.span_rows))

    if args.skip_reencode:
        reencoded = pd.DataFrame()
    else:
        reencoded = reencode_contexts(source, args.embedders, args.batch_size)
        reencoded.to_csv(OUT_DATA / "matched_context_reencoded.csv", index=False)

    paradox_path = Path(args.paradox_by_embedder)
    if paradox_path.exists():
        scaled_copy = pd.read_csv(paradox_path)
        scaled_copy.to_csv(OUT_DATA / "scaled_paradox_input_copy.csv", index=False)

    pieces = []
    if not reencoded.empty:
        pieces.append(summarize_reencoded(reencoded))
    scaled = summarize_scaled(paradox_path)
    if not scaled.empty:
        pieces.append(scaled)
    summary = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()
    summary.to_csv(OUT_RESULTS / "retriever_sanity_summary.csv", index=False)
    summary.to_csv(OUT_SOURCE / "retriever_sanity_summary.csv", index=False)
    write_report(summary, OUT_RESULTS / "retriever_sanity_report.md")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
