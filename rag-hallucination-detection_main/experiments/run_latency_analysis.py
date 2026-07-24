"""
Latency and Cost Analysis.
Reads existing per-query results and computes
latency breakdown by configuration.
Results saved to results/latency/
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import os
import json
import pandas as pd
import numpy as np
import glob

os.makedirs("results/latency", exist_ok=True)

rows = []

# Load all per-query CSVs
for pattern in ["results/ablation_chunk*.csv",
                "results/pubmedqa/ablation_chunk*.csv",
                "results/multimodel/*.csv",
                "results/reranker/*.csv"]:
    for fpath in glob.glob(pattern):
        fname = os.path.basename(fpath)
        if any(x in fname for x in ["scores","summary"]): continue
        try:
            df = pd.read_csv(fpath)
            if "latency_s" not in df.columns: continue

            # Parse metadata from filename
            parts = fname.replace(".csv","").split("_")

            # Detect source
            if "reranker" in fpath:
                source = "reranker"
                model   = parts[0]
                dataset = parts[1]
                chunk   = int([p for p in parts if p.startswith("chunk")][0].replace("chunk",""))
                condition = parts[-1]
                df["source"] = source
                df["model"] = model
                df["dataset"] = dataset
                df["chunk_size"] = chunk
                df["condition"] = condition
            elif "multimodel" in fpath:
                source = "multimodel"
                model   = parts[0]
                dataset = parts[1]
                chunk   = int([p for p in parts if p.startswith("chunk")][0].replace("chunk",""))
                condition = parts[-1]
                df["source"] = source
                df["model"] = model
                df["dataset"] = dataset
                df["chunk_size"] = chunk
                df["condition"] = condition
            else:
                source = "original"
                chunk   = int([p for p in parts if p.startswith("chunk")][0].replace("chunk",""))
                k       = int([p for p in parts if p.startswith("k")][0].replace("k",""))
                prompt  = parts[-1]
                dataset = "pubmedqa" if "pubmedqa" in fpath else "squad"
                df["source"] = source
                df["model"] = "mistral"
                df["dataset"] = dataset
                df["chunk_size"] = chunk
                df["condition"] = prompt

            rows.append(df[["latency_s","model","dataset","chunk_size","condition","source"]])
        except Exception as e:
            pass

df_all = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
print(f"[Latency] Loaded {len(df_all)} query records")

# ── Analysis ──────────────────────────────────────────────────────────────────
print("\n===== LATENCY BY MODEL AND DATASET =====")
by_model = df_all.groupby(["model","dataset"])["latency_s"].agg(["mean","std","min","max","count"]).round(2)
print(by_model)

print("\n===== LATENCY BY CHUNK SIZE =====")
by_chunk = df_all.groupby(["chunk_size"])["latency_s"].agg(["mean","std"]).round(2)
print(by_chunk)

print("\n===== LATENCY BY CONDITION (baseline vs reranked) =====")
rr_df = df_all[df_all.source=="reranker"]
if not rr_df.empty:
    by_cond = rr_df.groupby(["condition"])["latency_s"].agg(["mean","std","count"]).round(2)
    print(by_cond)

# ── Cost projection table ──────────────────────────────────────────────────────
print("\n===== COST PROJECTION (4,800 query experiment) =====")
configs = [
    ("chunk=256, k=3, no rerank", 3.5),
    ("chunk=512, k=3, no rerank", 4.5),
    ("chunk=1024, k=3, no rerank", 6.0),
    ("chunk=256, k=5, + rerank",  5.5),
    ("chunk=512, k=5, + rerank",  7.0),
    ("chunk=1024, k=5, + rerank", 9.0),
]
print(f"\n{'Configuration':<35} {'Per query':>10} {'100 queries':>12} {'1000 queries':>13}")
print("-"*75)
for label, lat in configs:
    print(f"{label:<35} {lat:>9.1f}s {lat*100/60:>10.1f}m {lat*1000/3600:>11.1f}h")

# ── Save ──────────────────────────────────────────────────────────────────────
latency_summary = df_all.groupby(["model","dataset","chunk_size"])["latency_s"].agg(
    mean_latency="mean", std_latency="std", n_queries="count"
).round(3).reset_index()
latency_summary.to_csv("results/latency/latency_summary.csv", index=False)

cost_df = pd.DataFrame(configs, columns=["configuration","latency_per_query_s"])
cost_df["100_queries_min"] = (cost_df.latency_per_query_s*100/60).round(1)
cost_df["1000_queries_hours"] = (cost_df.latency_per_query_s*1000/3600).round(2)
cost_df.to_csv("results/latency/cost_projection.csv", index=False)

print("\nSaved to results/latency/")