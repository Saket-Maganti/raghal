# Coherence Analysis — "Why Coherence Matters"

N_DOCS=30, N_QUESTIONS=30, MODEL=llama3, CHUNK=1024, TOP_K=3

## Spearman ρ between coherence metrics and faithfulness

| Dataset | Condition | Metric | ρ | p-value | n |
|---------|-----------|--------|:-:|:-------:|:-:|
| pubmedqa | baseline | retrieval_entropy | 0.332 | 0.073 | 30 |
| pubmedqa | baseline | mean_jaccard | 0.279 | 0.136 | 30 |
| pubmedqa | baseline | sim_spread | 0.244 | 0.195 | 30 |
| pubmedqa | baseline | embedding_variance | 0.242 | 0.197 | 30 |
| pubmedqa | baseline | mean_query_chunk_sim | 0.106 | 0.578 | 30 |
| pubmedqa | baseline | ccs | 0.011 | 0.954 | 30 |
| pubmedqa | baseline | semantic_continuity | 0.011 | 0.954 | 30 |
| pubmedqa | hcpc_v2 | embedding_variance | 0.336 | 0.069 | 30 |
| pubmedqa | hcpc_v2 | retrieval_entropy | 0.315 | 0.090 | 30 |
| pubmedqa | hcpc_v2 | sim_spread | 0.305 | 0.102 | 30 |
| pubmedqa | hcpc_v2 | mean_jaccard | 0.229 | 0.225 | 30 |
| pubmedqa | hcpc_v2 | mean_query_chunk_sim | 0.116 | 0.542 | 30 |
| pubmedqa | hcpc_v2 | ccs | 0.021 | 0.913 | 30 |
| pubmedqa | hcpc_v2 | semantic_continuity | 0.021 | 0.913 | 30 |
| squad | baseline | mean_query_chunk_sim | 0.210 | 0.265 | 30 |
| squad | baseline | ccs | 0.174 | 0.357 | 30 |
| squad | baseline | semantic_continuity | 0.174 | 0.357 | 30 |
| squad | baseline | mean_jaccard | -0.028 | 0.885 | 30 |
| squad | baseline | retrieval_entropy | -0.093 | 0.626 | 30 |
| squad | baseline | embedding_variance | -0.177 | 0.348 | 30 |
| squad | baseline | sim_spread | -0.248 | 0.186 | 30 |
| squad | hcpc_v2 | mean_query_chunk_sim | 0.323 | 0.082 | 30 |
| squad | hcpc_v2 | ccs | 0.313 | 0.092 | 30 |
| squad | hcpc_v2 | semantic_continuity | 0.313 | 0.092 | 30 |
| squad | hcpc_v2 | retrieval_entropy | 0.117 | 0.536 | 30 |
| squad | hcpc_v2 | mean_jaccard | 0.025 | 0.894 | 30 |
| squad | hcpc_v2 | embedding_variance | -0.020 | 0.915 | 30 |
| squad | hcpc_v2 | sim_spread | -0.197 | 0.297 | 30 |

## Condition means by dataset

### SQUAD

| Condition | Faithfulness | Halluc.% | CCS | Embed Var | Jaccard | Entropy |
|-----------|:----------:|:------:|:---:|:--------:|:-------:|:-------:|
| baseline | 0.8158 | 0.0 | 0.6057 | 0.0036 | 0.1396 | 0.5567 |
| hcpc_v2 | 0.8330 | 0.0 | 0.6057 | 0.0036 | 0.1396 | 0.5568 |

### PUBMEDQA

| Condition | Faithfulness | Halluc.% | CCS | Embed Var | Jaccard | Entropy |
|-----------|:----------:|:------:|:---:|:--------:|:-------:|:-------:|
| baseline | 0.5760 | 33.3 | 0.4875 | 0.0260 | 0.1239 | 0.4996 |
| hcpc_v2 | 0.5900 | 10.0 | 0.4871 | 0.0260 | 0.1239 | 0.5041 |

