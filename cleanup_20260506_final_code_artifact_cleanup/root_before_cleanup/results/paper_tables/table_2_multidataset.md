### Table 2 — Multi-dataset / multi-model validation

| dataset   | model   | condition   |   n_queries |   faith |   halluc |   refine_rate |      ccs |
|:----------|:--------|:------------|------------:|--------:|---------:|--------------:|---------:|
| hotpotqa  | qwen2.5 | baseline    |          30 |  0.6186 |   0.0333 |        0      | nan      |
| hotpotqa  | qwen2.5 | hcpc_v1     |          30 |  0.6041 |   0.1    |        0      | nan      |
| hotpotqa  | qwen2.5 | hcpc_v2     |          30 |  0.616  |   0.0667 |        0.3667 |   0.4116 |
| naturalqs | llama3  | baseline    |          60 |  0.6734 |   0.0667 |        0      | nan      |
| naturalqs | llama3  | hcpc_v1     |          60 |  0.6449 |   0.0333 |        0      | nan      |
| naturalqs | llama3  | hcpc_v2     |          60 |  0.6695 |   0.1    |        0.4833 |   0.6218 |
| naturalqs | mistral | baseline    |          60 |  0.674  |   0.1333 |        0      | nan      |
| naturalqs | mistral | hcpc_v1     |          60 |  0.6446 |   0.1167 |        0      | nan      |
| naturalqs | mistral | hcpc_v2     |          60 |  0.6746 |   0.15   |        0.4833 |   0.6218 |
| naturalqs | qwen2.5 | baseline    |          60 |  0.6456 |   0.1167 |        0      | nan      |
| naturalqs | qwen2.5 | hcpc_v1     |          60 |  0.6423 |   0.0333 |        0      | nan      |
| naturalqs | qwen2.5 | hcpc_v2     |          60 |  0.6659 |   0.05   |        0.4833 |   0.6218 |
| pubmedqa  | qwen2.5 | baseline    |          30 |  0.5926 |   0.0667 |        0      | nan      |
| pubmedqa  | qwen2.5 | hcpc_v1     |          30 |  0.6109 |   0.0667 |        0      | nan      |
| pubmedqa  | qwen2.5 | hcpc_v2     |          30 |  0.596  |   0.0333 |        0.7333 |   0.57   |
| squad     | qwen2.5 | baseline    |          30 |  0.8312 |   0      |        0      | nan      |
| squad     | qwen2.5 | hcpc_v1     |          30 |  0.685  |   0      |        0      | nan      |
| squad     | qwen2.5 | hcpc_v2     |          30 |  0.8265 |   0      |        0.3333 |   0.5551 |
| triviaqa  | qwen2.5 | baseline    |          30 |  0.6582 |   0.0333 |        0      | nan      |
| triviaqa  | qwen2.5 | hcpc_v1     |          30 |  0.6317 |   0.0333 |        0      | nan      |
| triviaqa  | qwen2.5 | hcpc_v2     |          30 |  0.6582 |   0.0333 |        0.4333 |   0.5726 |

