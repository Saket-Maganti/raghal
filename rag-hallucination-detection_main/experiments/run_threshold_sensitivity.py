import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import itertools
import os
import time
import numpy as np
import pandas as pd

from src.rag_pipeline import RAGPipeline
from src.hcpc_v2_retriever import HCPCv2Retriever
from src.coherence_metrics import compute_coherence_metrics
from src.data_loader import load_qasper
from src.pubmedqa_loader import load_pubmedqa


# ======================
# CONFIG (FOCUSED GRID)
# ======================
SIM_THRESHOLDS = [0.4, 0.5, 0.6]
CE_THRESHOLDS = [-0.2, -0.15, -0.1]
TOPK_PROTECTED = [1, 2, 3]

N_DOCS = 30
N_QUESTIONS_PER_CFG = 10
TOP_K = 5

OUTPUT_DIR = "results/threshold_sensitivity"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ======================
# PROXY SCORE
# ======================
def compute_proxy_score(ccs, emb_var, entropy, qsim):
    if ccs == -1 or emb_var < 0 or entropy < 0 or qsim == -1:
        return -1

    return (
        0.4 * ccs
        - 0.3 * emb_var
        - 0.2 * entropy
        + 0.1 * qsim
    ) * 10


# ======================
# SINGLE CONFIG
# ======================
def run_one_config(pipeline, qa_pairs, sim, ce, topk):

    hcpc = HCPCv2Retriever(
        pipeline,
        sim_threshold=sim,
        ce_threshold=ce,
        top_k_protected=topk,
    )

    ccs_list, proxy_list = [], []
    refined_counts = []

    for qa in qa_pairs[:N_QUESTIONS_PER_CFG]:
        docs, log = hcpc.retrieve(qa["question"])

        coh = compute_coherence_metrics(
            qa["question"], docs, pipeline.embeddings
        )

        ccs = coh.get("ccs", -1)
        emb_var = coh.get("embedding_variance", -1)
        entropy = coh.get("retrieval_entropy", -1)
        qsim = coh.get("mean_query_chunk_sim", -1)

        proxy = compute_proxy_score(ccs, emb_var, entropy, qsim)

        if ccs != -1:
            ccs_list.append(ccs)
        if proxy != -1:
            proxy_list.append(proxy)

        refined_counts.append(log.get("refined", 0))

    return {
        "sim": sim,
        "ce": ce,
        "topk": topk,
        "mean_ccs": np.mean(ccs_list) if ccs_list else -1,
        "ccs_var": np.var(ccs_list) if len(ccs_list) > 1 else 0,
        "proxy_score": np.mean(proxy_list) if proxy_list else -1,
        "pct_refined": np.mean(refined_counts) * 100 if refined_counts else 0,
    }


# ======================
# DATASET RUN
# ======================
def run_dataset(name, docs, qa):

    print(f"\n===== {name.upper()} =====")

    pipeline = RAGPipeline(
        top_k=TOP_K,
        embed_model="sentence-transformers/all-MiniLM-L6-v2"
    )

    pipeline.index_documents(docs[:N_DOCS])

    results = []

    configs = list(itertools.product(
        SIM_THRESHOLDS, CE_THRESHOLDS, TOPK_PROTECTED
    ))

    for i, (sim, ce, topk) in enumerate(configs, 1):
        print(f"[{i}/{len(configs)}] sim={sim} ce={ce} topk={topk}", end=" ")

        t0 = time.time()
        row = run_one_config(pipeline, qa, sim, ce, topk)
        row["time"] = round(time.time() - t0, 2)

        results.append(row)

        print(
            f"→ proxy={row['proxy_score']:.3f} "
            f"ccs={row['mean_ccs']:.3f} "
            f"ref%={row['pct_refined']:.1f}"
        )

    return pd.DataFrame(results)


# ======================
# MAIN
# ======================
def main():

    print("🚀 STARTING FINAL THRESHOLD SWEEP")

    squad_docs, squad_qa = load_qasper(max_papers=N_DOCS)
    pub_docs, pub_qa = load_pubmedqa(max_papers=N_DOCS)

    df1 = run_dataset("squad", squad_docs, squad_qa)
    df2 = run_dataset("pubmedqa", pub_docs, pub_qa)

    df1["dataset"] = "squad"
    df2["dataset"] = "pubmedqa"

    df = pd.concat([df1, df2])
    df.to_csv(os.path.join(OUTPUT_DIR, "sweep_results.csv"), index=False)

    print("\n✅ RESULTS SAVED")

    # ======================
    # FILTER + RANK
    # ======================
    df_filtered = df[(df["topk"] > 1) & (df["pct_refined"] > 0)]

    print("\n🏆 FINAL CONFIGS (MEANINGFUL ONLY):")

    for ds in ["squad", "pubmedqa"]:
        sub = df_filtered[df_filtered["dataset"] == ds]

        best = sub.sort_values(
            ["proxy_score", "pct_refined"],
            ascending=[False, False]
        ).head(3)

        print(f"\n{ds.upper()}")
        print(best[[
            "sim", "ce", "topk",
            "proxy_score", "mean_ccs", "pct_refined"
        ]])

    print("\n🎯 Next: run LLM ablation on these configs")


# ======================
# ENTRY
# ======================
if __name__ == "__main__":
    main()