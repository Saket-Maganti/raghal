import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
df = pd.read_csv('results/multimodel/summary.csv')
print('Completed configs:', len(df))
print(df[['model','dataset','chunk_size','top_k','prompt_strategy']].to_string(index=False))
