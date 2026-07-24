### Gap 2 — Prompt template robustness

| dataset   | model   | template   |   faith_base |   faith_v1 |   faith_v2 |   paradox_drop |   v2_recovery |   ref_paradox_drop |   delta_vs_ref |   stable |
|:----------|:--------|:-----------|-------------:|-----------:|-----------:|---------------:|--------------:|-------------------:|---------------:|---------:|
| hotpotqa  | mistral | concise    |       0.6239 |     0.6631 |     0.6186 |        -0.0392 |       -0.0445 |                nan |            nan |      nan |
| hotpotqa  | mistral | cot        |       0.641  |     0.6323 |     0.6395 |         0.0087 |        0.0072 |                nan |            nan |      nan |
| hotpotqa  | mistral | expert     |       0.6127 |     0.6158 |     0.6093 |        -0.0031 |       -0.0065 |                nan |            nan |      nan |
| hotpotqa  | mistral | strict     |       0.6034 |     0.6239 |     0.6074 |        -0.0205 |       -0.0165 |                nan |            nan |      nan |
| pubmedqa  | mistral | concise    |       0.5788 |     0.5622 |     0.5854 |         0.0166 |        0.0232 |                nan |            nan |      nan |
| pubmedqa  | mistral | cot        |       0.5816 |     0.5786 |     0.5668 |         0.003  |       -0.0118 |                nan |            nan |      nan |
| pubmedqa  | mistral | expert     |       0.5551 |     0.5527 |     0.5646 |         0.0024 |        0.0119 |                nan |            nan |      nan |
| pubmedqa  | mistral | strict     |       0.5943 |     0.545  |     0.5897 |         0.0493 |        0.0447 |                nan |            nan |      nan |
| squad     | mistral | concise    |       0.6773 |     0.7138 |     0.6899 |        -0.0365 |       -0.0239 |                nan |            nan |      nan |
| squad     | mistral | cot        |       0.7947 |     0.7837 |     0.8082 |         0.011  |        0.0245 |                nan |            nan |      nan |
| squad     | mistral | expert     |       0.7725 |     0.7184 |     0.789  |         0.0541 |        0.0706 |                nan |            nan |      nan |
| squad     | mistral | strict     |       0.7916 |     0.7082 |     0.804  |         0.0834 |        0.0958 |                nan |            nan |      nan |

