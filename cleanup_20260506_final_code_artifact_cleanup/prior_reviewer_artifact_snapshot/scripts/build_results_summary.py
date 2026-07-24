"""
scripts/build_results_summary.py — single all-results aggregator
================================================================

Walks every results subdirectory and emits a single CSV + markdown table
showing the paradox magnitude (and HCPC-v2 recovery, where defined) for
every experimental cell across the entire project. Useful for spotting
trends across experiments and as the canonical "paste this into a
slide" table.

Aggregates from:
    results/multidataset/summary.csv
    results/multiseed/paradox_variance.csv (if present)
    results/raptor/raptor_vs_hcpc.csv (if present)
    results/longform/summary.csv (if present)
    results/noise_injection/coherence_vs_noise.csv (if present)
    results/prompt_ablation/summary.csv (if present)
    results/subchunk_sensitivity/paradox_by_sub.csv (if present)
    results/topk_sensitivity/paradox_by_k.csv
    results/frontier_scale/paradox_by_scale.csv
    results/quantization_sensitivity/paradox_by_quant.csv
    results/temperature_sensitivity/paradox_by_temp.csv (if present)
    results/crossencoder_sensitivity/paradox_by_ce.csv

Outputs:
    results/all_results_summary.csv
    results/all_results_summary.md

Usage:
    python3 scripts/build_results_summary.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT_CSV = RESULTS / "all_results_summary.csv"
OUT_MD = RESULTS / "all_results_summary.md"


def _safe_read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as exc:
        print(f"[summary] skip {path.name}: {exc}")
        return pd.DataFrame()


def _row(experiment: str, condition_label: str, paradox: float = None,
         recovery: float = None, n: int = None,
         extra: Dict = None) -> Dict:
    base = {
        "experiment": experiment,
        "condition_label": condition_label,
        "paradox": round(paradox, 4) if paradox is not None else None,
        "v2_recovery": round(recovery, 4) if recovery is not None else None,
        "n_queries": n,
    }
    if extra:
        base.update(extra)
    return base


def _collect_multidataset() -> List[Dict]:
    df = _safe_read(RESULTS / "multidataset" / "summary.csv")
    if df.empty:
        return []
    rows = []
    for (ds, mdl), sub in df.groupby(["dataset", "model"]):
        try:
            base = float(sub[sub["condition"] == "baseline"]["faith"].iloc[0])
            v1 = float(sub[sub["condition"] == "hcpc_v1"]["faith"].iloc[0])
            v2 = float(sub[sub["condition"] == "hcpc_v2"]["faith"].iloc[0])
            n = int(sub["n_queries"].iloc[0])
        except (IndexError, KeyError):
            continue
        rows.append(_row("multidataset", f"{ds} × {mdl}",
                          paradox=base - v1, recovery=v2 - v1, n=n))
    return rows


def _collect_topk() -> List[Dict]:
    df = _safe_read(RESULTS / "topk_sensitivity" / "paradox_by_k.csv")
    if df.empty:
        return []
    rows = []
    for _, r in df.iterrows():
        rows.append(_row("topk", f"{r['dataset']} × k={int(r['k'])}",
                          paradox=r["paradox"], recovery=r["v2_recovery"]))
    return rows


def _collect_frontier() -> List[Dict]:
    df = _safe_read(RESULTS / "frontier_scale" / "paradox_by_scale.csv")
    if df.empty:
        return []
    # column is 'paradox_drop' here, not 'paradox'
    par_col = "paradox_drop" if "paradox_drop" in df.columns else "paradox"
    rows = []
    for _, r in df.iterrows():
        rows.append(_row("frontier", f"{r['dataset']} × {r['model']} ({r['scale']})",
                          paradox=r[par_col], recovery=r["v2_recovery"]))
    return rows


def _collect_quant() -> List[Dict]:
    df = _safe_read(RESULTS / "quantization_sensitivity" / "paradox_by_quant.csv")
    if df.empty:
        return []
    rows = []
    for _, r in df.iterrows():
        extra = {"latency_s": round(float(r.get("latency_base", 0)), 2)}
        rows.append(_row("quantization",
                         f"{r['dataset']} × {r['quant']}",
                         paradox=r["paradox"], recovery=r["v2_recovery"],
                         extra=extra))
    return rows


def _collect_temperature() -> List[Dict]:
    df = _safe_read(RESULTS / "temperature_sensitivity" / "paradox_by_temp.csv")
    if df.empty:
        return []
    rows = []
    for _, r in df.iterrows():
        rows.append(_row("temperature",
                         f"{r['dataset']} × T={r['temperature']}",
                         paradox=r["paradox"], recovery=r["v2_recovery"]))
    return rows


def _collect_crossencoder() -> List[Dict]:
    df = _safe_read(RESULTS / "crossencoder_sensitivity" / "paradox_by_ce.csv")
    if df.empty:
        return []
    rows = []
    for _, r in df.iterrows():
        ce_short = str(r["reranker"]).split("/")[-1]
        rows.append(_row("crossencoder",
                         f"{r['dataset']} × {ce_short}",
                         paradox=r["paradox"], recovery=r["v2_recovery"]))
    return rows


def _collect_raptor() -> List[Dict]:
    df = _safe_read(RESULTS / "raptor" / "raptor_vs_hcpc.csv")
    if df.empty:
        return []
    rows = []
    for _, r in df.iterrows():
        rows.append(_row("raptor",
                         f"{r['dataset']}: HCPC-v1 vs RAPTOR",
                         paradox=r.get("delta_faith", None),
                         recovery=None))
    return rows


def _collect_subchunk() -> List[Dict]:
    df = _safe_read(RESULTS / "subchunk_sensitivity" / "paradox_by_sub.csv")
    if df.empty:
        return []
    rows = []
    for _, r in df.iterrows():
        rows.append(_row("subchunk",
                         f"{r['dataset']} × sub={int(r['sub_chunk'])}",
                         paradox=r.get("paradox_drop"),
                         recovery=None))
    return rows


def _collect_noise() -> List[Dict]:
    df = _safe_read(RESULTS / "noise_injection" / "coherence_vs_noise.csv")
    if df.empty:
        return []
    rows = []
    for _, r in df.iterrows():
        rows.append(_row("noise",
                         f"{r['dataset']}: paradox vs noise",
                         paradox=r.get("paradox_drop"),
                         recovery=None,
                         extra={"noise_slope": round(float(r.get("noise_slope", 0)), 4)}))
    return rows


def _collect_longform() -> List[Dict]:
    df = _safe_read(RESULTS / "longform" / "summary.csv")
    if df.empty:
        return []
    rows = []
    for ds, sub in df.groupby("dataset"):
        try:
            b = float(sub[sub["condition"] == "baseline"]["faith"].iloc[0])
            v1 = float(sub[sub["condition"] == "hcpc_v1"]["faith"].iloc[0])
            v2 = float(sub[sub["condition"] == "hcpc_v2"]["faith"].iloc[0])
        except (IndexError, KeyError):
            continue
        rows.append(_row("longform", ds,
                          paradox=b - v1, recovery=v2 - v1))
    return rows


def main() -> None:
    rows: List[Dict] = []
    rows += _collect_multidataset()
    rows += _collect_frontier()
    rows += _collect_topk()
    rows += _collect_quant()
    rows += _collect_temperature()
    rows += _collect_crossencoder()
    rows += _collect_raptor()
    rows += _collect_subchunk()
    rows += _collect_noise()
    rows += _collect_longform()

    if not rows:
        raise SystemExit("[summary] no result CSVs found anywhere")

    df = pd.DataFrame(rows)
    df = df.sort_values(["experiment", "condition_label"]).reset_index(drop=True)

    OUT_CSV.write_text(df.to_csv(index=False))
    print(f"[summary] wrote {OUT_CSV.relative_to(ROOT)} ({len(df)} rows)")

    md_lines = [
        "# All results — at a glance",
        "",
        f"Auto-generated by `scripts/build_results_summary.py` from "
        f"every `results/*/paradox_*.csv` and `summary.csv` on "
        f"the project. {len(df)} cells across "
        f"{df['experiment'].nunique()} experiments.",
        "",
    ]

    for exp, sub in df.groupby("experiment"):
        md_lines.append(f"## {exp}")
        md_lines.append("")
        md_lines.append(sub.drop(columns=["experiment"]).to_markdown(index=False))
        md_lines.append("")

    OUT_MD.write_text("\n".join(md_lines))
    print(f"[summary] wrote {OUT_MD.relative_to(ROOT)}")
    print()
    print(df.groupby("experiment")["paradox"].agg(["count", "mean", "min", "max"]).round(4).to_string())


if __name__ == "__main__":
    main()
