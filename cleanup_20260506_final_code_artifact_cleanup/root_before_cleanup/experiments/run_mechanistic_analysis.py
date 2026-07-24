"""
run_mechanistic_analysis.py  — §7.5 Mechanistic Evidence
========================================================

Tests the mechanistic hypothesis behind the refinement paradox:

    Fragmented retrieval (HCPC-v1 style) increases attention entropy over the
    retrieved passages and shifts attention mass away from retrieved tokens
    and toward parametric positions (BOS, instruction, query prefix).

Matched pair design:
  - coherent   : baseline 1024-token chunks, no refinement
  - fragmented : the same query, but the passages have been refined and
                 replaced with 256-token sub-spans (HCPC-v1 behavior)

The matched pairs come from two sources:
  (a) The existing Phase-6 HCPC v2 ablation run (baseline vs hcpc_v1)
      — we reuse the raw retrieval from those logs if available.
  (b) The adversarial case set (control vs drift / disjoint / contradict)
      — the adversarial categories naturally give us fragmented-feeling
      contexts with a clean matched control.

Outputs (results/mechanistic/):
  per_pair.csv       — one row per (case, condition) with aggregate metrics
  entropy_by_layer.csv — entropy averaged over heads, per-layer
  retrieved_mass_by_layer.csv — retrieved-attention mass per-layer
  top_k_attributions.jsonl — qualitative per-token attribution samples
  summary.md         — human-readable digest

Run (requires a GPU):
  python3 experiments/run_mechanistic_analysis.py \
      --model mistralai/Mistral-7B-Instruct-v0.2 \
      --source adversarial \
      --device cuda
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import os
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from src.mechanistic import AttentionProbe, AttentionAnalysis
from src.adversarial_cases import load_all_cases

OUTPUT_DIR = "results/mechanistic"


def build_pairs_from_adversarial() -> List[Dict]:
    """
    For every adversarial case in disjoint/contradict/drift, pair it with
    its matched control (same query). Returns a list of dicts:
        {
          "pair_id":   "...",
          "condition": "coherent" | "fragmented",
          "query":     "...",
          "passages":  [str, ...]
        }
    """
    all_cases = load_all_cases()
    ctrl_by_query = {c.query: c for c in all_cases.get("control", [])}
    pairs: List[Dict] = []
    for cat in ("disjoint", "contradict", "drift"):
        for adv in all_cases.get(cat, []):
            ctrl = ctrl_by_query.get(adv.query)
            if ctrl is None:
                continue
            pairs.append({
                "pair_id":   adv.case_id,
                "condition": "fragmented",
                "category":  cat,
                "query":     adv.query,
                "passages":  [p["text"] for p in adv.passages],
            })
            pairs.append({
                "pair_id":   adv.case_id,
                "condition": "coherent",
                "category":  cat,
                "query":     ctrl.query,
                "passages":  [p["text"] for p in ctrl.passages],
            })
    return pairs


def build_pairs_from_hcpc_logs(logs_dir: str) -> List[Dict]:
    """
    Pull matched (baseline, hcpc_v1) retrievals from the Phase-6 ablation
    logs. Each entry in the failure logs has `retrieved_context` and `query`;
    we pair baseline vs v1 entries on identical queries.
    """
    import glob
    pairs: List[Dict] = []
    base_path = os.path.join(logs_dir, "*_baseline_logs.json")
    v1_path   = os.path.join(logs_dir, "*_hcpc_v1_logs.json")
    base_files = sorted(glob.glob(base_path))
    v1_files   = sorted(glob.glob(v1_path))
    base_by_ds: Dict[str, Dict[str, Dict]] = {}
    for bf in base_files:
        ds = os.path.basename(bf).replace("_baseline_logs.json", "")
        with open(bf) as fh:
            entries = json.load(fh)
        by_q = {e["query"]: e for e in entries if isinstance(e, dict) and "query" in e}
        base_by_ds[ds] = by_q
    for vf in v1_files:
        ds = os.path.basename(vf).replace("_hcpc_v1_logs.json", "")
        with open(vf) as fh:
            entries = json.load(fh)
        for e in entries:
            if not isinstance(e, dict) or "query" not in e:
                continue
            q = e["query"]
            base = base_by_ds.get(ds, {}).get(q)
            if base is None:
                continue
            # Split retrieved_context into passages by the pipeline delimiter
            base_passages = [p.strip() for p in base["retrieved_context"].split("\n\n---\n\n") if p.strip()]
            frag_passages = [p.strip() for p in e["retrieved_context"].split("\n\n---\n\n") if p.strip()]
            pair_id = f"{ds}_{abs(hash(q)) % 10_000_000}"
            pairs.append({
                "pair_id":   pair_id,
                "condition": "coherent",
                "category":  ds,
                "query":     q,
                "passages":  base_passages,
            })
            pairs.append({
                "pair_id":   pair_id,
                "condition": "fragmented",
                "category":  ds,
                "query":     q,
                "passages":  frag_passages,
            })
    return pairs


def summarize_pair(pair: Dict, analysis: AttentionAnalysis) -> Dict:
    agg = analysis.aggregate()
    return {
        "pair_id":            pair["pair_id"],
        "category":           pair["category"],
        "condition":          pair["condition"],
        "query":              pair["query"],
        "input_tokens":       analysis.input_token_count,
        "output_tokens":      analysis.output_token_count,
        "mean_entropy":       round(agg["mean_entropy"], 4),
        "mean_retrieved_mass": round(agg["mean_retrieved_mass"], 4),
        "mean_parametric_mass": round(agg["mean_parametric_mass"], 4),
        "p25_retrieved_mass": round(agg["p25_retrieved_mass"], 4),
        "p75_retrieved_mass": round(agg["p75_retrieved_mass"], 4),
        "output_text":        analysis.output_text,
    }


def save_layer_breakdown(rows: List[Dict], analyses: List[AttentionAnalysis], out_dir: str) -> None:
    """
    Produce a layer-wise averaged view of entropy and retrieved mass so the
    paper figure can show the depth at which the coherent/fragmented split
    opens up.
    """
    if not analyses:
        return
    n_layers = analyses[0].attention_entropy.shape[0]
    ent_by_layer: List[Dict] = []
    mass_by_layer: List[Dict] = []
    for row, a in zip(rows, analyses):
        for L in range(n_layers):
            ent = float(np.nanmean(a.attention_entropy[L]))
            mass = float(np.nanmean(a.retrieved_mass[L]))
            ent_by_layer.append({
                "pair_id":   row["pair_id"],
                "category":  row["category"],
                "condition": row["condition"],
                "layer":     L,
                "mean_entropy": round(ent, 4),
            })
            mass_by_layer.append({
                "pair_id":   row["pair_id"],
                "category":  row["category"],
                "condition": row["condition"],
                "layer":     L,
                "mean_retrieved_mass": round(mass, 4),
            })
    pd.DataFrame(ent_by_layer).to_csv(
        os.path.join(out_dir, "entropy_by_layer.csv"), index=False
    )
    pd.DataFrame(mass_by_layer).to_csv(
        os.path.join(out_dir, "retrieved_mass_by_layer.csv"), index=False
    )


def write_summary_md(rows: List[Dict], out_path: str) -> None:
    df = pd.DataFrame(rows)
    if df.empty:
        with open(out_path, "w") as fh:
            fh.write("# Mechanistic Analysis — No results produced.\n")
        return
    agg = df.groupby(["category", "condition"])[
        ["mean_entropy", "mean_retrieved_mass", "mean_parametric_mass"]
    ].mean().round(4)
    lines = ["# Mechanistic Analysis — Summary", "", "## Per-category × condition means", ""]
    lines.append(agg.to_markdown())
    lines.append("")
    lines.append("## Hypothesis check")
    lines.append("")
    lines.append(
        "Under the coherence hypothesis, `fragmented` rows should show "
        "**higher** mean_entropy and **lower** mean_retrieved_mass than "
        "the matched `coherent` rows within each category."
    )
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="mistralai/Mistral-7B-Instruct-v0.2")
    parser.add_argument("--source", choices=["adversarial", "hcpc_logs", "both"], default="adversarial")
    parser.add_argument("--logs_dir", default="results/hcpc_v2/logs")
    parser.add_argument("--device", default=None)
    parser.add_argument("--max_new_tokens", type=int, default=48)
    parser.add_argument("--max_pairs", type=int, default=0,
                        help="If >0, analyze at most this many pairs (for smoke tests).")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pairs: List[Dict] = []
    if args.source in ("adversarial", "both"):
        pairs.extend(build_pairs_from_adversarial())
    if args.source in ("hcpc_logs", "both"):
        pairs.extend(build_pairs_from_hcpc_logs(args.logs_dir))

    if args.max_pairs and len(pairs) > args.max_pairs:
        pairs = pairs[: args.max_pairs]

    print(f"[Mech] Analyzing {len(pairs)} (case, condition) items...")

    probe = AttentionProbe(model_name=args.model, device=args.device)

    rows: List[Dict] = []
    analyses: List[AttentionAnalysis] = []
    attrib_jsonl_path = os.path.join(OUTPUT_DIR, "top_k_attributions.jsonl")
    with open(attrib_jsonl_path, "w") as attrib_fh:
        for i, pair in enumerate(pairs):
            print(f"[Mech] [{i+1}/{len(pairs)}] {pair['pair_id']} ({pair['condition']})")
            a = probe.analyze(
                retrieved_passages=pair["passages"],
                query=pair["query"],
                max_new_tokens=args.max_new_tokens,
            )
            rows.append(summarize_pair(pair, a))
            analyses.append(a)
            # Sparse attribution dump (only keep first N output tokens)
            attrib_fh.write(json.dumps({
                "pair_id":   pair["pair_id"],
                "condition": pair["condition"],
                "category":  pair["category"],
                "query":     pair["query"],
                "output":    a.output_text,
                "top_k_attribution": a.top_k_attribution[:16],
            }) + "\n")

    pd.DataFrame(rows).to_csv(
        os.path.join(OUTPUT_DIR, "per_pair.csv"), index=False
    )
    save_layer_breakdown(rows, analyses, OUTPUT_DIR)
    write_summary_md(rows, os.path.join(OUTPUT_DIR, "summary.md"))
    print(f"[Mech] Outputs -> {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
