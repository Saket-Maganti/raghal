import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import os, json, glob
import pandas as pd
import numpy as np
from scipy.stats import f_oneway, ttest_ind
from itertools import combinations

os.makedirs("results/stats", exist_ok=True)

def load_results(pattern, ds):
    dfs = []
    for f in glob.glob(pattern):
        # Skip aggregate summary/scores files — they lack per-query faithfulness_score
        if f.endswith("_scores.csv") or f.endswith("_summary.csv"):
            continue
        df = pd.read_csv(f)
        if "faithfulness_score" not in df.columns:
            continue
        dfs.append(df)
    combined = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    combined["dataset"] = ds
    return combined

squad_df  = load_results("results/ablation_chunk*_k*_*.csv", "squad")
pubmed_df = load_results("results/pubmedqa/ablation_chunk*_k*_*.csv", "pubmedqa")
print(f"SQuAD: {len(squad_df)} | PubMedQA: {len(pubmed_df)}")

def run_tests(df, factor, outcome):
    groups = df.groupby(factor)[outcome].apply(list)
    keys = list(groups.index)
    f_stat, p_val = f_oneway(*[groups[k] for k in keys])
    pairs = list(combinations(keys, 2))
    pairwise = []
    for a, b in pairs:
        t, p_raw = ttest_ind(groups[a], groups[b], equal_var=False)
        p_bonf = min(float(p_raw) * len(pairs), 1.0)
        d = (np.mean(groups[a]) - np.mean(groups[b])) / np.sqrt(
            (np.std(groups[a])**2 + np.std(groups[b])**2) / 2)
        pairwise.append({
            "a": str(a), "b": str(b),
            "mean_a": round(float(np.mean(groups[a])), 4),
            "mean_b": round(float(np.mean(groups[b])), 4),
            "diff": round(float(np.mean(groups[a]) - np.mean(groups[b])), 4),
            "p_bonf": round(p_bonf, 6),
            "cohen_d": round(float(d), 4),
            "sig": bool(p_bonf < 0.05)
        })
    return {
        "factor": factor,
        "f": round(float(f_stat), 4),
        "p": round(float(p_val), 6),
        "sig": bool(p_val < 0.05),
        "means": {str(k): round(float(np.mean(groups[k])), 4) for k in keys},
        "pairwise": pairwise
    }

results = {}
print("\n===== ANOVA RESULTS =====")
for factor in ["chunk_size", "prompt_strategy", "top_k"]:
    for df, ds in [(squad_df, "squad"), (pubmed_df, "pubmedqa")]:
        r = run_tests(df, factor, "faithfulness_score")
        results[f"{factor}_{ds}"] = r
        sig = "SIGNIFICANT" if r["sig"] else "not significant"
        print(f"\n{ds} | {factor}: F={r['f']}, p={r['p']} -> {sig}")
        print(f"  means: {r['means']}")
        for pair in r["pairwise"]:
            s = "sig" if pair["sig"] else "ns"
            print(f"  {pair['a']} vs {pair['b']}: "
                  f"diff={pair['diff']:+.4f}, "
                  f"p_bonf={pair['p_bonf']:.4f} [{s}], "
                  f"d={pair['cohen_d']:.3f}")

with open("results/stats/significance_tests.json", "w") as f:
    json.dump(results, f, indent=2)

rows = []
for key, r in results.items():
    rows.append({
        "test": key, "factor": r["factor"],
        "F": r["f"], "p": r["p"], "significant": r["sig"]
    })
pd.DataFrame(rows).to_csv("results/stats/summary.csv", index=False)
print("\nSaved to results/stats/")