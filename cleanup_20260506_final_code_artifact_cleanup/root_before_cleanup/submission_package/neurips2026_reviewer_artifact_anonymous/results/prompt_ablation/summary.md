# Prompt-template ablation (NeurIPS Gap 2)

Four prompt templates (strict, CoT, concise, expert-role) × three retrieval conditions × three datasets, to test whether the coherence paradox and v2 recovery depend on the specific prompt used in `src/rag_pipeline.py`.

## Aggregated metrics per (dataset, template, condition)

| dataset   | model   | template   | condition   |   n_queries |   faith |   halluc |    sim |   refine_rate |      ccs |   latency |
|:----------|:--------|:-----------|:------------|------------:|--------:|---------:|-------:|--------------:|---------:|----------:|
| hotpotqa  | mistral | concise    | baseline    |          30 |  0.6239 |   0.2333 | 0.6462 |        0      | nan      |    3.232  |
| hotpotqa  | mistral | concise    | hcpc_v1     |          30 |  0.6631 |   0.1667 | 0.6697 |        0      | nan      |    1.6063 |
| hotpotqa  | mistral | concise    | hcpc_v2     |          30 |  0.6186 |   0.2667 | 0.6461 |        0.1    |   1      |    2.5953 |
| hotpotqa  | mistral | cot        | baseline    |          30 |  0.641  |   0.1333 | 0.6099 |        0      | nan      |    6.1917 |
| hotpotqa  | mistral | cot        | hcpc_v1     |          30 |  0.6323 |   0.2    | 0.6286 |        0      | nan      |    4.7393 |
| hotpotqa  | mistral | cot        | hcpc_v2     |          30 |  0.6395 |   0.1667 | 0.6098 |        0.3667 |   0.4116 |    5.5163 |
| hotpotqa  | mistral | expert     | baseline    |          30 |  0.6127 |   0.2667 | 0.6462 |        0      | nan      |    4.9893 |
| hotpotqa  | mistral | expert     | hcpc_v1     |          30 |  0.6158 |   0.2333 | 0.6697 |        0      | nan      |    2.6777 |
| hotpotqa  | mistral | expert     | hcpc_v2     |          30 |  0.6093 |   0.2333 | 0.6461 |        0.1    |   1      |    4.097  |
| hotpotqa  | mistral | strict     | baseline    |          30 |  0.6034 |   0.2    | 0.552  |        0      | nan      |    4.9817 |
| hotpotqa  | mistral | strict     | hcpc_v1     |          30 |  0.6239 |   0.2333 | 0.5699 |        0      | nan      |    2.944  |
| hotpotqa  | mistral | strict     | hcpc_v2     |          30 |  0.6074 |   0.2333 | 0.5519 |        0.5667 |   0.3684 |    4.4017 |
| pubmedqa  | mistral | concise    | baseline    |          30 |  0.5788 |   0.3333 | 0.7278 |        0      | nan      |    5.8907 |
| pubmedqa  | mistral | concise    | hcpc_v1     |          30 |  0.5622 |   0.4    | 0.7568 |        0      | nan      |    1.6767 |
| pubmedqa  | mistral | concise    | hcpc_v2     |          30 |  0.5854 |   0.3333 | 0.7276 |        0.1667 |   1      |    3.4373 |
| pubmedqa  | mistral | cot        | baseline    |          30 |  0.5816 |   0.2    | 0.6531 |        0      | nan      |   11.4013 |
| pubmedqa  | mistral | cot        | hcpc_v1     |          30 |  0.5786 |   0.2667 | 0.6783 |        0      | nan      |    7.083  |
| pubmedqa  | mistral | cot        | hcpc_v2     |          30 |  0.5668 |   0.3    | 0.6526 |        0.7333 |   0.57   |   10.0607 |
| pubmedqa  | mistral | expert     | baseline    |          30 |  0.5551 |   0.2    | 0.7278 |        0      | nan      |   10.457  |
| pubmedqa  | mistral | expert     | hcpc_v1     |          30 |  0.5527 |   0.2667 | 0.7568 |        0      | nan      |    5.6213 |
| pubmedqa  | mistral | expert     | hcpc_v2     |          30 |  0.5646 |   0.2667 | 0.7276 |        0.1667 |   1      |    7.8453 |
| pubmedqa  | mistral | strict     | baseline    |          30 |  0.5943 |   0.2333 | 0.5166 |        0      | nan      |    8.7183 |
| pubmedqa  | mistral | strict     | hcpc_v1     |          30 |  0.545  |   0.3333 | 0.5471 |        0      | nan      |    5.1087 |
| pubmedqa  | mistral | strict     | hcpc_v2     |          30 |  0.5897 |   0.2    | 0.5168 |        0.9667 |   0.3091 |    8.019  |
| squad     | mistral | concise    | baseline    |          30 |  0.6773 |   0.1    | 0.6343 |        0      | nan      |    2.1077 |
| squad     | mistral | concise    | hcpc_v1     |          30 |  0.7138 |   0.1333 | 0.6236 |        0      | nan      |    1.2647 |
| squad     | mistral | concise    | hcpc_v2     |          30 |  0.6899 |   0.1    | 0.6342 |        0.1667 |   1      |    3.5187 |
| squad     | mistral | cot        | baseline    |          30 |  0.7947 |   0.0333 | 0.6154 |        0      | nan      |    4.1157 |
| squad     | mistral | cot        | hcpc_v1     |          30 |  0.7837 |   0      | 0.6172 |        0      | nan      |    4.2277 |
| squad     | mistral | cot        | hcpc_v2     |          30 |  0.8082 |   0      | 0.6152 |        0.3333 |   0.5551 |    5.312  |
| squad     | mistral | expert     | baseline    |          30 |  0.7725 |   0.0333 | 0.6343 |        0      | nan      |    3.2163 |
| squad     | mistral | expert     | hcpc_v1     |          30 |  0.7184 |   0      | 0.6236 |        0      | nan      |    2.9503 |
| squad     | mistral | expert     | hcpc_v2     |          30 |  0.789  |   0      | 0.6342 |        0.1667 |   1      |    4.6347 |
| squad     | mistral | strict     | baseline    |          30 |  0.7916 |   0.0333 | 0.5877 |        0      | nan      |    3.1353 |
| squad     | mistral | strict     | hcpc_v1     |          30 |  0.7082 |   0.1333 | 0.6008 |        0      | nan      |    2.482  |
| squad     | mistral | strict     | hcpc_v2     |          30 |  0.804  |   0      | 0.5879 |        0.5333 |   0.5425 |    3.783  |

## Paradox magnitude vs reference (multidataset summary)

`ref_paradox_drop` = paradox gap reported in `results/multidataset/summary.csv` (strict prompt).  
`delta_vs_ref` = this run's paradox_drop − ref_paradox_drop.  
`stable` = |delta_vs_ref| ≤ 0.03 (target: True across all templates).

| dataset   | model   | template   |   faith_base |   faith_v1 |   faith_v2 |   paradox_drop |   v2_recovery | ref_paradox_drop   | delta_vs_ref   | stable   |
|:----------|:--------|:-----------|-------------:|-----------:|-----------:|---------------:|--------------:|:-------------------|:---------------|:---------|
| hotpotqa  | mistral | concise    |       0.6239 |     0.6631 |     0.6186 |        -0.0392 |       -0.0445 |                    |                |          |
| hotpotqa  | mistral | cot        |       0.641  |     0.6323 |     0.6395 |         0.0087 |        0.0072 |                    |                |          |
| hotpotqa  | mistral | expert     |       0.6127 |     0.6158 |     0.6093 |        -0.0031 |       -0.0065 |                    |                |          |
| hotpotqa  | mistral | strict     |       0.6034 |     0.6239 |     0.6074 |        -0.0205 |       -0.0165 |                    |                |          |
| pubmedqa  | mistral | concise    |       0.5788 |     0.5622 |     0.5854 |         0.0166 |        0.0232 |                    |                |          |
| pubmedqa  | mistral | cot        |       0.5816 |     0.5786 |     0.5668 |         0.003  |       -0.0118 |                    |                |          |
| pubmedqa  | mistral | expert     |       0.5551 |     0.5527 |     0.5646 |         0.0024 |        0.0119 |                    |                |          |
| pubmedqa  | mistral | strict     |       0.5943 |     0.545  |     0.5897 |         0.0493 |        0.0447 |                    |                |          |
| squad     | mistral | concise    |       0.6773 |     0.7138 |     0.6899 |        -0.0365 |       -0.0239 |                    |                |          |
| squad     | mistral | cot        |       0.7947 |     0.7837 |     0.8082 |         0.011  |        0.0245 |                    |                |          |
| squad     | mistral | expert     |       0.7725 |     0.7184 |     0.789  |         0.0541 |        0.0706 |                    |                |          |
| squad     | mistral | strict     |       0.7916 |     0.7082 |     0.804  |         0.0834 |        0.0958 |                    |                |          |

If `stable == True` across all 4 × 3 = 12 cells, the paradox is not an artifact of the production prompt and survives the standard taxonomy of RAG prompt styles.