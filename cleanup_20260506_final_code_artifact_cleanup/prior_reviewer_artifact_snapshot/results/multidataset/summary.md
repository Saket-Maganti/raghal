# Multi-dataset / multi-model validation

## Aggregated metrics

| dataset   | model   | condition   |   n_queries |   faith |   halluc |    sim |   refine_rate |      ccs |
|:----------|:--------|:------------|------------:|--------:|---------:|-------:|--------------:|---------:|
| hotpotqa  | qwen2.5 | baseline    |          30 |  0.6186 |   0.0333 | 0.6099 |        0      | nan      |
| hotpotqa  | qwen2.5 | hcpc_v1     |          30 |  0.6041 |   0.1    | 0.6286 |        0      | nan      |
| hotpotqa  | qwen2.5 | hcpc_v2     |          30 |  0.616  |   0.0667 | 0.6098 |        0.3667 |   0.4116 |
| naturalqs | llama3  | baseline    |          60 |  0.6734 |   0.0667 | 0.5937 |        0      | nan      |
| naturalqs | llama3  | hcpc_v1     |          60 |  0.6449 |   0.0333 | 0.6398 |        0      | nan      |
| naturalqs | llama3  | hcpc_v2     |          60 |  0.6695 |   0.1    | 0.5932 |        0.4833 |   0.6218 |
| naturalqs | mistral | baseline    |          60 |  0.674  |   0.1333 | 0.5937 |        0      | nan      |
| naturalqs | mistral | hcpc_v1     |          60 |  0.6446 |   0.1167 | 0.6398 |        0      | nan      |
| naturalqs | mistral | hcpc_v2     |          60 |  0.6746 |   0.15   | 0.5932 |        0.4833 |   0.6218 |
| naturalqs | qwen2.5 | baseline    |          60 |  0.6456 |   0.1167 | 0.5937 |        0      | nan      |
| naturalqs | qwen2.5 | hcpc_v1     |          60 |  0.6423 |   0.0333 | 0.6398 |        0      | nan      |
| naturalqs | qwen2.5 | hcpc_v2     |          60 |  0.6659 |   0.05   | 0.5932 |        0.4833 |   0.6218 |
| pubmedqa  | qwen2.5 | baseline    |          30 |  0.5926 |   0.0667 | 0.6531 |        0      | nan      |
| pubmedqa  | qwen2.5 | hcpc_v1     |          30 |  0.6109 |   0.0667 | 0.6783 |        0      | nan      |
| pubmedqa  | qwen2.5 | hcpc_v2     |          30 |  0.596  |   0.0333 | 0.6526 |        0.7333 |   0.57   |
| squad     | qwen2.5 | baseline    |          30 |  0.8312 |   0      | 0.6154 |        0      | nan      |
| squad     | qwen2.5 | hcpc_v1     |          30 |  0.685  |   0      | 0.6172 |        0      | nan      |
| squad     | qwen2.5 | hcpc_v2     |          30 |  0.8265 |   0      | 0.6152 |        0.3333 |   0.5551 |
| triviaqa  | qwen2.5 | baseline    |          30 |  0.6582 |   0.0333 | 0.6044 |        0      | nan      |
| triviaqa  | qwen2.5 | hcpc_v1     |          30 |  0.6317 |   0.0333 | 0.6488 |        0      | nan      |
| triviaqa  | qwen2.5 | hcpc_v2     |          30 |  0.6582 |   0.0333 | 0.6045 |        0.4333 |   0.5726 |

## Coherence paradox per (dataset, model)
`paradox_drop` = faith_baseline − faith_v1 (positive = paradox confirmed)
`v2_recovery` = faith_v2 − faith_v1   (positive = v2 helps)

| dataset   | model   |   faith_baseline |   faith_v1 |   faith_v2 |   paradox_drop |   v2_recovery |   halluc_baseline |   halluc_v1 |   halluc_v2 |
|:----------|:--------|-----------------:|-----------:|-----------:|---------------:|--------------:|------------------:|------------:|------------:|
| hotpotqa  | qwen2.5 |           0.6186 |     0.6041 |     0.616  |         0.0145 |        0.0119 |            0.0333 |      0.1    |      0.0667 |
| naturalqs | llama3  |           0.6734 |     0.6449 |     0.6695 |         0.0285 |        0.0246 |            0.0667 |      0.0333 |      0.1    |
| naturalqs | mistral |           0.674  |     0.6446 |     0.6746 |         0.0294 |        0.03   |            0.1333 |      0.1167 |      0.15   |
| naturalqs | qwen2.5 |           0.6456 |     0.6423 |     0.6659 |         0.0033 |        0.0236 |            0.1167 |      0.0333 |      0.05   |
| pubmedqa  | qwen2.5 |           0.5926 |     0.6109 |     0.596  |        -0.0183 |       -0.0149 |            0.0667 |      0.0667 |      0.0333 |
| squad     | qwen2.5 |           0.8312 |     0.685  |     0.8265 |         0.1462 |        0.1415 |            0      |      0      |      0      |
| triviaqa  | qwen2.5 |           0.6582 |     0.6317 |     0.6582 |         0.0265 |        0.0265 |            0.0333 |      0.0333 |      0.0333 |