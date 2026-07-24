# Quantization sensitivity ablation (Phase 5 #6)

Mistral-7B-Instruct quantized at Q4_0 / Q5_K_M / Q8_0 via Ollama.
SQuAD + PubMedQA, 30 queries each, 3 conditions per quant.

## Aggregated metrics

| dataset   | quant   | condition   |   n_queries |   faith |   halluc |    sim |   refine_rate |      ccs |   latency |
|:----------|:--------|:------------|------------:|--------:|---------:|-------:|--------------:|---------:|----------:|
| pubmedqa  | q4_0    | baseline    |          30 |  0.6014 |   0.1333 | 0.6531 |        0      | nan      |    8.6207 |
| pubmedqa  | q4_0    | hcpc_v1     |          30 |  0.5814 |   0.2667 | 0.6783 |        0      | nan      |    4.5763 |
| pubmedqa  | q4_0    | hcpc_v2     |          30 |  0.5796 |   0.2667 | 0.6526 |        0.7333 |   0.57   |    7.2293 |
| pubmedqa  | q5_K_M  | baseline    |          30 |  0.548  |   0.3333 | 0.5166 |        0      | nan      |   18.008  |
| pubmedqa  | q5_K_M  | hcpc_v1     |          30 |  0.5517 |   0.3    | 0.5471 |        0      | nan      |    9.5717 |
| pubmedqa  | q5_K_M  | hcpc_v2     |          30 |  0.5412 |   0.3667 | 0.5168 |        0.9667 |   0.3091 |   16.682  |
| pubmedqa  | q8_0    | baseline    |          30 |  0.5683 |   0.2    | 0.5166 |        0      | nan      |   13.7307 |
| pubmedqa  | q8_0    | hcpc_v1     |          30 |  0.5688 |   0.1667 | 0.5471 |        0      | nan      |    7.8827 |
| pubmedqa  | q8_0    | hcpc_v2     |          30 |  0.5568 |   0.2667 | 0.5168 |        0.9667 |   0.3091 |   13.3593 |
| squad     | q4_0    | baseline    |          30 |  0.7907 |   0      | 0.6154 |        0      | nan      |    2.7187 |
| squad     | q4_0    | hcpc_v1     |          30 |  0.6959 |   0.1    | 0.6172 |        0      | nan      |    2.2687 |
| squad     | q4_0    | hcpc_v2     |          30 |  0.7826 |   0      | 0.6152 |        0.3333 |   0.5551 |    3.4513 |
| squad     | q5_K_M  | baseline    |          30 |  0.8087 |   0      | 0.5877 |        0      | nan      |    5.1563 |
| squad     | q5_K_M  | hcpc_v1     |          30 |  0.7205 |   0      | 0.6008 |        0      | nan      |    2.769  |
| squad     | q5_K_M  | hcpc_v2     |          30 |  0.8056 |   0      | 0.5879 |        0.5333 |   0.5425 |    5.627  |
| squad     | q8_0    | baseline    |          30 |  0.8132 |   0.0333 | 0.5877 |        0      | nan      |    5.6223 |
| squad     | q8_0    | hcpc_v1     |          30 |  0.7205 |   0      | 0.6008 |        0      | nan      |    3.1243 |
| squad     | q8_0    | hcpc_v2     |          30 |  0.7975 |   0.0333 | 0.5879 |        0.5333 |   0.5425 |    5.979  |

## Paradox by quantization

| dataset   | quant   |   faith_base |   faith_v1 |   faith_v2 |   paradox |   v2_recovery |   latency_base |
|:----------|:--------|-------------:|-----------:|-----------:|----------:|--------------:|---------------:|
| pubmedqa  | q4_0    |       0.6014 |     0.5814 |     0.5796 |    0.02   |       -0.0018 |         8.6207 |
| pubmedqa  | q5_K_M  |       0.548  |     0.5517 |     0.5412 |   -0.0037 |       -0.0105 |        18.008  |
| pubmedqa  | q8_0    |       0.5683 |     0.5688 |     0.5568 |   -0.0005 |       -0.012  |        13.7307 |
| squad     | q4_0    |       0.7907 |     0.6959 |     0.7826 |    0.0948 |        0.0867 |         2.7187 |
| squad     | q5_K_M  |       0.8087 |     0.7205 |     0.8056 |    0.0882 |        0.0851 |         5.1563 |
| squad     | q8_0    |       0.8132 |     0.7205 |     0.7975 |    0.0927 |        0.077  |         5.6223 |

Headline: SQuAD paradox is **stable across all 3 quants** 
(+0.095 / +0.088 / +0.093). HCPC-v2 recovery is also stable 
(+0.087 / +0.085 / +0.077). PubMedQA paradox is near-zero at 
all quants, consistent with the domain-mismatched-encoder story. 
Practitioners running Q4 for cost get the same paradox/recovery as Q8.