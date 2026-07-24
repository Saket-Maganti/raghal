import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import glob
import os

os.makedirs("results/qualitative", exist_ok=True)

# Load all per-question results
dfs = []
for f in glob.glob("results/ablation_chunk*_k*_*.csv"):
    df = pd.read_csv(f)
    dfs.append(df)

squad_df = pd.concat(dfs, ignore_index=True)

# Load pubmedqa
pdfs = []
for f in glob.glob("results/pubmedqa/ablation_chunk*_k*_*.csv"):
    df = pd.read_csv(f)
    pdfs.append(df)
pubmed_df = pd.concat(pdfs, ignore_index=True)

print("=== WORST HALLUCINATIONS (faithfulness < 0.4) ===")
bad = squad_df[squad_df["faithfulness_score"] < 0.4].sort_values("faithfulness_score")
print(f"Found {len(bad)} hallucinated answers on SQuAD\n")
for _, row in bad.head(5).iterrows():
    print(f"Q: {row['question']}")
    print(f"A: {str(row['answer'])[:300]}")
    print(f"Faithfulness: {row['faithfulness_score']:.4f} | chunk={row['chunk_size']} k={row['top_k']} prompt={row['prompt_strategy']}")
    print()

print("=== CHUNK=256 vs CHUNK=1024 SAME QUESTION ===")
# Find questions answered in both chunk=256 and chunk=1024
sq_256  = squad_df[squad_df["chunk_size"]==256][["question","answer","faithfulness_score","chunk_size"]].copy()
sq_1024 = squad_df[squad_df["chunk_size"]==1024][["question","answer","faithfulness_score","chunk_size"]].copy()
merged = sq_256.merge(sq_1024, on="question", suffixes=("_256","_1024"))
merged["improvement"] = merged["faithfulness_score_1024"] - merged["faithfulness_score_256"]
top_improvements = merged.nlargest(5, "improvement")

print(f"\nTop 5 questions where chunk=1024 most improved over chunk=256:\n")
for _, row in top_improvements.iterrows():
    print(f"Q: {row['question']}")
    print(f"chunk=256  (faith={row['faithfulness_score_256']:.4f}): {str(row['answer_256'])[:200]}")
    print(f"chunk=1024 (faith={row['faithfulness_score_1024']:.4f}): {str(row['answer_1024'])[:200]}")
    print(f"Improvement: +{row['improvement']:.4f}")
    print()

# Save
merged.to_csv("results/qualitative/chunk_comparison.csv", index=False)
bad.head(20).to_csv("results/qualitative/worst_hallucinations.csv", index=False)
print("Saved to results/qualitative/")