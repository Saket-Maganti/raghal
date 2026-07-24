"""
build_rag_vs_zeroshot_table.py — NeurIPS Gap 3
==============================================

Reshapes already-collected data into a 2×2 table answering the question
reviewers keep asking: *when does RAG help at all, and when does adding a
stronger retriever matter?*

This script does NOT launch new LLM runs.  It consumes:

    results/zeroshot/summary.csv           — closed-book, no retrieval
    results/multi_retriever/summary.csv    — RAG across 4 embedders
    results/multidataset/summary.csv       — baseline RAG on full datasets
                                             (mistral, llama3, qwen2.5)

and emits a compact matrix:

                       | Weak retriever  | Strong retriever
    -------------------+-----------------+-----------------
    Open domain (SQuAD)| faith_Δ_weak    | faith_Δ_strong
    Closed (PubMedQA)  | faith_Δ_weak    | faith_Δ_strong

where `faith_Δ = faith(RAG) − faith(zeroshot)`.  The sign of each cell tells
us whether retrieval is a net win at that (domain, retriever-strength)
operating point.  This is the 2×2 the NeurIPS reviewer asked for.

We also emit the coherence-paradox magnitude per cell (baseline − hcpc_v1)
so the reader can see whether the paradox itself depends on retriever
strength — a claim made implicitly in the multi_retriever ablation but
never tabulated against the zero-shot baseline.

Retriever-strength mapping:
    weak   = minilm       (22 M params, all-MiniLM-L6-v2)
    strong = gte-large    (335 M params, thenlper/gte-large)

Outputs (results/rag_vs_zeroshot/):
    table_2x2.csv            — headline 2×2 (domain × retriever_strength)
    per_cell_detail.csv      — per (model, domain, retriever): all metrics
    paradox_vs_strength.csv  — paradox magnitude per retriever strength
    summary.md               — narrative + tables for §Results

Run (fast, just reads CSVs):

    python3 experiments/build_rag_vs_zeroshot_table.py
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List, Optional

import pandas as pd


OUTPUT_DIR = "results/rag_vs_zeroshot"

ZEROSHOT_CSV       = "results/zeroshot/summary.csv"
MULTI_RETRIEVER_CSV = "results/multi_retriever/summary.csv"

# Domain classification — aligned with the closed-book / open-book split
# used throughout the paper.
DOMAIN_MAP: Dict[str, str] = {
    "squad":     "open",
    "hotpotqa":  "open",
    "triviaqa":  "open",
    "naturalqs": "open",
    "pubmedqa":  "closed",
}

# Embedder → retriever-strength mapping.  We pick the extremes of the
# multi_retriever ablation to make the 2×2 a clean weak-vs-strong contrast.
STRENGTH_MAP: Dict[str, str] = {
    "minilm":    "weak",
    "bge-large": "strong",   # secondary strong option
    "e5-large":  "strong",   # secondary strong option
    "gte-large": "strong",   # canonical strong
}

# Among multiple "strong" embedders, prefer gte-large as the canonical cell
# value.  (bge and e5 still appear in per_cell_detail for robustness.)
CANONICAL_STRONG = "gte-large"


def _load_or_die(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise SystemExit(
            f"[RAGvsZS] required input missing: {path}\n"
            f"         run the corresponding experiment first."
        )
    return pd.read_csv(path)


def build_zero_shot_lookup(zs: pd.DataFrame) -> Dict:
    """(model, dataset) → {nli_faithfulness, hallucination_rate, n}."""
    out = {}
    for _, row in zs.iterrows():
        key = (row["model"], row["dataset"])
        out[key] = {
            "zs_faith":  float(row["nli_faithfulness"]),
            "zs_halluc": float(row["hallucination_rate"]),
            "zs_n":      int(row["n_samples"]),
        }
    return out


def build_rag_lookup(mr: pd.DataFrame) -> Dict:
    """(dataset, embedder, condition) → row as dict."""
    out = {}
    for _, row in mr.iterrows():
        key = (row["dataset"], row["embedder"], row["condition"])
        out[key] = row.to_dict()
    return out


def build_per_cell_detail(
    zs_lookup: Dict, rag_lookup: Dict, model: str = "mistral",
) -> pd.DataFrame:
    """One row per (dataset, embedder) with zero-shot and RAG metrics."""
    rows: List[Dict] = []
    datasets = sorted({d for (d, _, _) in rag_lookup})
    embedders = sorted({e for (_, e, _) in rag_lookup})
    for ds in datasets:
        domain = DOMAIN_MAP.get(ds, "unknown")
        zs = zs_lookup.get((model, ds))
        if zs is None:
            # Zero-shot not collected for this (model, dataset).
            continue
        for emb in embedders:
            strength = STRENGTH_MAP.get(emb, "unknown")
            base = rag_lookup.get((ds, emb, "baseline"))
            v1   = rag_lookup.get((ds, emb, "hcpc_v1"))
            v2   = rag_lookup.get((ds, emb, "hcpc_v2"))
            if base is None:
                continue
            rag_faith = float(base["faith"])
            row = {
                "model":              model,
                "dataset":            ds,
                "domain":             domain,
                "embedder":           emb,
                "retriever_strength": strength,
                "zs_faith":           round(zs["zs_faith"], 4),
                "rag_faith":          round(rag_faith, 4),
                "delta_faith":        round(rag_faith - zs["zs_faith"], 4),
                "rag_helps":          rag_faith > zs["zs_faith"],
                "zs_halluc":          round(zs["zs_halluc"], 4),
                "rag_halluc":         round(float(base["halluc"]), 4),
                "rag_sim":            round(float(base["sim"]), 4),
                "rag_latency":        round(float(base["latency"]), 3),
                "paradox_drop":       (round(float(base["faith"])
                                              - float(v1["faith"]), 4)
                                        if v1 is not None else None),
                "v2_recovery":        (round(float(v2["faith"])
                                              - float(v1["faith"]), 4)
                                        if (v1 is not None and v2 is not None)
                                        else None),
            }
            rows.append(row)
    return pd.DataFrame(rows)


def build_2x2(detail: pd.DataFrame) -> pd.DataFrame:
    """Collapse to the headline 2×2 (domain × retriever_strength).

    For "strong" we use the canonical gte-large row if present, else fall
    back to the mean of all strong embedders.  For "weak" we use minilm.
    """
    if detail.empty:
        return detail
    rows: List[Dict] = []
    for domain in ("open", "closed"):
        d_sub = detail[detail["domain"] == domain]
        if d_sub.empty:
            continue
        for strength in ("weak", "strong"):
            s_sub = d_sub[d_sub["retriever_strength"] == strength]
            if s_sub.empty:
                continue
            if strength == "strong" and (s_sub["embedder"] == CANONICAL_STRONG).any():
                pick = s_sub[s_sub["embedder"] == CANONICAL_STRONG]
            else:
                pick = s_sub
            zs_faith      = pick["zs_faith"].mean()
            rag_faith     = pick["rag_faith"].mean()
            delta_faith   = pick["delta_faith"].mean()
            paradox_drop  = pick["paradox_drop"].mean()
            v2_recovery   = pick["v2_recovery"].mean()
            rows.append({
                "domain":              domain,
                "retriever_strength":  strength,
                "n_datasets":          int(pick["dataset"].nunique()),
                "embedders_used":      ",".join(sorted(pick["embedder"].unique())),
                "zs_faith":            round(float(zs_faith), 4),
                "rag_faith":           round(float(rag_faith), 4),
                "delta_faith":         round(float(delta_faith), 4),
                "rag_helps":           bool(delta_faith > 0),
                "paradox_drop":        (round(float(paradox_drop), 4)
                                         if pd.notna(paradox_drop) else None),
                "v2_recovery":         (round(float(v2_recovery), 4)
                                         if pd.notna(v2_recovery) else None),
            })
    return pd.DataFrame(rows)


def build_paradox_vs_strength(detail: pd.DataFrame) -> pd.DataFrame:
    """Per retriever_strength: does paradox magnitude depend on it?"""
    if detail.empty:
        return detail
    rows = []
    for strength, sub in detail.groupby("retriever_strength"):
        rows.append({
            "retriever_strength": strength,
            "n_cells":            len(sub),
            "mean_paradox_drop":  round(float(sub["paradox_drop"].mean()), 4)
                                    if sub["paradox_drop"].notna().any() else None,
            "std_paradox_drop":   round(float(sub["paradox_drop"].std()), 4)
                                    if sub["paradox_drop"].notna().sum() > 1 else None,
            "mean_v2_recovery":   round(float(sub["v2_recovery"].mean()), 4)
                                    if sub["v2_recovery"].notna().any() else None,
            "mean_delta_faith":   round(float(sub["delta_faith"].mean()), 4),
        })
    return pd.DataFrame(rows)


def write_summary_md(
    detail: pd.DataFrame,
    table: pd.DataFrame,
    paradox: pd.DataFrame,
    out_path: str,
) -> None:
    lines = [
        "# RAG vs zero-shot (NeurIPS Gap 3)", "",
        "Answers the reviewer question: *does retrieval help, and under what "
        "conditions?*  Reshapes existing `results/zeroshot/`, "
        "`results/multi_retriever/`, and `results/multidataset/` outputs — "
        "no new LLM calls.", "",
        "Domain split: `open` = SQuAD / HotpotQA / TriviaQA / NaturalQS, "
        "`closed` = PubMedQA.  ",
        "Retriever strength split: `weak` = MiniLM-L6 (22 M params), "
        "`strong` = GTE-large / BGE-large / E5-large (335 M params).", "",
        "## Headline 2×2 (domain × retriever strength)", "",
        "`delta_faith` = faith(RAG, baseline condition) − faith(zero-shot).  "
        "Positive = RAG helps.  "
        "`rag_helps` flags the sign.", "",
        table.to_markdown(index=False) if not table.empty else "(no data)",
        "",
        "## Does the coherence paradox depend on retriever strength?", "",
        "`mean_paradox_drop` is the average faith drop from baseline to "
        "HCPC-v1 across datasets at that retriever strength.  A strength-"
        "invariant paradox is strong evidence that the effect is driven by "
        "the LM's coherence preference rather than by retriever noise.", "",
        paradox.to_markdown(index=False) if not paradox.empty else "(no data)",
        "",
        "## Per-cell detail", "",
        "One row per (dataset, embedder).  `paradox_drop` = faith_baseline "
        "− faith_v1.  `v2_recovery` = faith_v2 − faith_v1.", "",
        detail.to_markdown(index=False) if not detail.empty else "(no data)",
    ]
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="mistral",
                        help="Model to cross-reference between zero-shot and "
                             "multi_retriever (multi_retriever is mistral-only).")
    parser.add_argument("--zeroshot_csv", type=str, default=ZEROSHOT_CSV)
    parser.add_argument("--multi_retriever_csv", type=str, default=MULTI_RETRIEVER_CSV)
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    zs  = _load_or_die(args.zeroshot_csv)
    mr  = _load_or_die(args.multi_retriever_csv)

    zs_lookup  = build_zero_shot_lookup(zs)
    rag_lookup = build_rag_lookup(mr)

    detail = build_per_cell_detail(zs_lookup, rag_lookup, model=args.model)
    detail.to_csv(os.path.join(OUTPUT_DIR, "per_cell_detail.csv"), index=False)

    table = build_2x2(detail)
    table.to_csv(os.path.join(OUTPUT_DIR, "table_2x2.csv"), index=False)

    paradox = build_paradox_vs_strength(detail)
    paradox.to_csv(os.path.join(OUTPUT_DIR, "paradox_vs_strength.csv"), index=False)

    write_summary_md(detail, table, paradox,
                     os.path.join(OUTPUT_DIR, "summary.md"))
    print(f"[RAGvsZS] outputs -> {OUTPUT_DIR}/")
    if not table.empty:
        print("\n[RAGvsZS] Headline 2x2:")
        print(table.to_string(index=False))


if __name__ == "__main__":
    main()
