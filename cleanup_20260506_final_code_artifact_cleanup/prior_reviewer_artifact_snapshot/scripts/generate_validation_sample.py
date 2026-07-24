"""
Human Validation Sample Generator.

Generates 50 answer samples from the best and worst configurations
for human grading. Saves as an Excel sheet you can fill in.

Run: python generate_validation_sample.py
Then open results/human_validation/validation_sheet.csv,
grade each row (0 or 1 in the 'human_faithful' column),
and run: python compute_nli_human_correlation.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import os
import pandas as pd
import random

os.makedirs("results/human_validation", exist_ok=True)
random.seed(42)

# Load existing per-config results
configs_to_sample = [
    # Best SQuAD config
    ("results/ablation_chunk1024_k5_strict.csv", "squad", "chunk=1024,k=5,strict", "best"),
    # Worst SQuAD config
    ("results/ablation_chunk256_k3_strict.csv",  "squad", "chunk=256,k=3,strict",  "worst"),
    # Best PubMedQA config
    ("results/pubmedqa/ablation_chunk512_k3_cot.csv",    "pubmedqa", "chunk=512,k=3,cot",    "best"),
    # Worst PubMedQA config
    ("results/pubmedqa/ablation_chunk256_k5_strict.csv", "pubmedqa", "chunk=256,k=5,strict", "worst"),
]

samples = []
per_config = 13  # ~13 × 4 configs = 52, we'll take exactly 50

for path, dataset, config_label, tier in configs_to_sample:
    if not os.path.exists(path):
        print(f"Warning: {path} not found, skipping")
        continue

    df = pd.read_csv(path)
    n = min(per_config, len(df))
    sample = df.sample(n=n, random_state=42)

    for _, row in sample.iterrows():
        samples.append({
            "id": len(samples) + 1,
            "dataset": dataset,
            "config": config_label,
            "tier": tier,
            "question": row.get("question", ""),
            "context": str(row.get("context", ""))[:500] + "...",
            "answer": str(row.get("answer", ""))[:400],
            "nli_faithfulness_score": round(float(row.get("faithfulness_score", 0)), 4),
            "nli_label": row.get("nli_label", row.get("label", "")),
            # Grader fills this in:
            "human_faithful": "",   # 1 = faithful, 0 = hallucinated
            "human_notes": "",      # optional comments
        })

# Shuffle so grader doesn't see config pattern
random.shuffle(samples)
for i, s in enumerate(samples):
    s["id"] = i + 1

df_out = pd.DataFrame(samples[:50])
out_path = "results/human_validation/validation_sheet.csv"
df_out.to_csv(out_path, index=False)

print(f"Validation sheet saved to: {out_path}")
print(f"Total samples: {len(df_out)}")
print(f"\nInstructions:")
print(f"1. Open results/human_validation/validation_sheet.csv")
print(f"2. For each row, read the question, context, and answer")
print(f"3. Fill in 'human_faithful' column: 1 if answer is faithful to context, 0 if not")
print(f"4. Save and run: python compute_nli_human_correlation.py")
print(f"\nConfig breakdown:")
print(df_out['config'].value_counts())