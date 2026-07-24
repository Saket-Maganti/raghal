import pandas as pd
import os

path = 'results/human_disagreement_expansion/annotation_batch_disagreement_100.csv'
df = pd.read_csv(path)

cols_to_add = [
    'human_label_rater1',
    'human_confidence_rater1',
    'human_notes_rater1',
    'human_label_rater2',
    'human_confidence_rater2',
    'human_notes_rater2',
    'adjudicated_label',
    'adjudicated_confidence',
    'adjudication_notes'
]

for col in cols_to_add:
    if col not in df.columns:
        df[col] = None

df.to_csv(path, index=False)
print(f"Updated {path} with new columns.")

# Generate rater files
rater_cols = [
    'example_id', 'question', 'retrieved_context', 'generated_answer', 
    'gold_answer', 'condition', 'disagreement_type'
]

# Rater 1
df_rater1 = df[rater_cols].copy()
df_rater1['human_label'] = None
df_rater1['human_confidence'] = None
df_rater1['human_notes'] = None
df_rater1.to_csv('results/human_disagreement_expansion/human_eval_rater1.csv', index=False)

# Rater 2
df_rater2 = df[rater_cols].copy()
df_rater2['human_label'] = None
df_rater2['human_confidence'] = None
df_rater2['human_notes'] = None
df_rater2.to_csv('results/human_disagreement_expansion/human_eval_rater2.csv', index=False)

# Adjudication template
adj_cols = rater_cols + [
    'human_label_rater1', 'human_label_rater2', 
    'adjudicated_label', 'adjudicated_confidence', 'adjudication_notes'
]
df_adj = df[adj_cols].copy()
df_adj.to_csv('results/human_disagreement_expansion/human_eval_adjudication_template.csv', index=False)

print("Generated rater and adjudication files.")
