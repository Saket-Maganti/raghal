"""
experiments/build_final_tables.py — paper-ready table builder
==============================================================

Concatenates every result CSV produced in the repo into one long-form
dataframe and emits the exact Markdown tables referenced in §Results +
§Analysis of the paper.  Run after all the Phase 1 + Phase 2 sweeps have
landed; rebuilds everything in <10 s.

Outputs
-------
    results/paper_tables/
        table_1_headtohead.md          — Table 1  (baseline vs HCPC vs CRAG vs Self-RAG)
        table_2_multidataset.md        — Table 2  (6 datasets × 3 models)
        table_3_multi_retriever.md     — Table 3  (paradox by embedder)
        table_4_raptor.md              — Table 4  (RAPTOR head-to-head)
        table_5_longform.md            — Table 5  (QASPER + MS-MARCO)
        table_6_frontier.md            — Table 6  (Groq 70B scale check)
        table_7_variance.md            — Table 7  (multi-seed variance)
        table_8_gap1_noise.md          — Gap 1    (noise vs coherence)
        table_9_gap2_prompt.md         — Gap 2    (prompt robustness)
        table_10_gap3_zeroshot.md      — Gap 3    (RAG vs zero-shot 2x2)
        table_11_mech_classifier.md    — Mech probe → classifier (AUC)
        table_12_deployment.md         — Deployment Pareto
        ALL_TABLES.md                  — concatenation, one file per paper
        missing.md                     — what's not yet available

Design
------
Every entry in TABLES maps:
    (paper_table_name, source_csv_path, md_renderer, required_columns)

A missing source CSV is *not* an error — we write a stub into `missing.md`
so the paper write-up knows which experiments still need to land.  That
way this script is safe to run mid-experiment.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT_DIR = ROOT / "results" / "paper_tables"


# ─────────────────────────────────────────────────────────────────────────────
# Renderers — each takes a DataFrame, returns Markdown string
# ─────────────────────────────────────────────────────────────────────────────

def _md(df: pd.DataFrame, caption: str) -> str:
    if df.empty:
        return f"### {caption}\n\n_(empty — source CSV had no rows)_\n\n"
    return f"### {caption}\n\n{df.to_markdown(index=False)}\n\n"


def render_headtohead(df: pd.DataFrame) -> str:
    keep = ["dataset", "condition", "n", "faith", "halluc", "sim", "latency"]
    df = df[[c for c in keep if c in df.columns]].copy()
    return _md(df, "Table 1 — Head-to-head retrievers")


def render_multidataset(df: pd.DataFrame) -> str:
    keep = ["dataset", "model", "condition", "n_queries",
            "faith", "halluc", "refine_rate", "ccs"]
    df = df[[c for c in keep if c in df.columns]].copy()
    return _md(df, "Table 2 — Multi-dataset / multi-model validation")


def render_multi_retriever(df: pd.DataFrame) -> str:
    return _md(df, "Table 3 — Paradox by embedder")


def render_raptor(df: pd.DataFrame) -> str:
    return _md(df, "Table 4 — RAPTOR head-to-head")


def render_longform(df: pd.DataFrame) -> str:
    return _md(df, "Table 5 — Long-form generation (QASPER + MS-MARCO)")


def render_frontier(df: pd.DataFrame) -> str:
    return _md(df, "Table 6 — Frontier-scale (Groq 70B / Mixtral)")


def render_variance(df: pd.DataFrame) -> str:
    return _md(df, "Table 7 — Multi-seed variance (reviewer error bars)")


def render_noise(df: pd.DataFrame) -> str:
    return _md(df, "Gap 1 — Coherence vs noise ablation")


def render_prompt(df: pd.DataFrame) -> str:
    return _md(df, "Gap 2 — Prompt template robustness")


def render_zeroshot(df: pd.DataFrame) -> str:
    return _md(df, "Gap 3 — RAG vs zero-shot (open/closed × open/closed)")


def render_mech(df: pd.DataFrame) -> str:
    return _md(df, "Mechanistic probe → hallucination classifier")


def render_deployment(df: pd.DataFrame) -> str:
    return _md(df, "Deployment Pareto (latency vs faith)")


# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────

TABLES: List[Tuple[str, str, Callable[[pd.DataFrame], str]]] = [
    ("table_1_headtohead",     "results/headtohead/summary.csv",                   render_headtohead),
    ("table_2_multidataset",   "results/multidataset/summary.csv",                 render_multidataset),
    ("table_3_multi_retriever","results/multi_retriever/paradox_by_embedder.csv",  render_multi_retriever),
    ("table_4_raptor",         "results/raptor/raptor_vs_hcpc.csv",                render_raptor),
    ("table_5_longform",       "results/longform/paradox_longform.csv",            render_longform),
    ("table_6_frontier",       "results/frontier_scale/paradox_by_scale.csv",      render_frontier),
    ("table_7_variance",       "results/multiseed/variance_summary.csv",           render_variance),
    ("table_8_gap1_noise",     "results/noise_injection/coherence_vs_noise.csv",   render_noise),
    ("table_9_gap2_prompt",    "results/prompt_ablation/paradox_by_prompt.csv",    render_prompt),
    ("table_10_gap3_zeroshot", "results/rag_vs_zeroshot/table_2x2.csv",            render_zeroshot),
    ("table_11_mech_classifier","results/mech_classifier/cv_results.csv",          render_mech),
    ("table_12_deployment",    "results/deployment_figure/pareto_summary.csv",     render_deployment),
]


# ─────────────────────────────────────────────────────────────────────────────
# Driver
# ─────────────────────────────────────────────────────────────────────────────

def _safe_read(rel: str) -> Optional[pd.DataFrame]:
    p = ROOT / rel
    if not p.exists():
        return None
    try:
        return pd.read_csv(p)
    except Exception as exc:
        print(f"[tables] {rel}: read error {exc}")
        return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_md_parts: List[str] = ["# All paper-ready tables\n",
                               "Generated by `experiments/build_final_tables.py`.\n"]
    missing: List[str] = []
    ok_count = 0

    for name, rel, renderer in TABLES:
        df = _safe_read(rel)
        if df is None:
            missing.append(f"- `{rel}` — for {name}")
            # Write a stub so paper-side tooling can still `\input` something.
            (OUT_DIR / f"{name}.md").write_text(
                f"### {name}\n\n_(result not yet available: {rel})_\n"
            )
            continue
        md = renderer(df)
        (OUT_DIR / f"{name}.md").write_text(md)
        all_md_parts.append(md)
        ok_count += 1
        print(f"[tables] ok  {name}  ({len(df)} rows)")

    (OUT_DIR / "ALL_TABLES.md").write_text("\n".join(all_md_parts))
    if missing:
        (OUT_DIR / "missing.md").write_text(
            "# Missing result sources\n\n"
            "These CSVs were not found.  Run the corresponding experiment "
            "or update the path in `experiments/build_final_tables.py`.\n\n"
            + "\n".join(missing) + "\n"
        )
    else:
        # Ensure a stale missing.md doesn't linger.
        p = OUT_DIR / "missing.md"
        if p.exists():
            p.unlink()

    print(f"\n[tables] wrote {ok_count}/{len(TABLES)} tables → {OUT_DIR}")
    if missing:
        print(f"[tables] {len(missing)} tables still missing — see "
              f"{OUT_DIR / 'missing.md'}")


if __name__ == "__main__":
    main()
