# Top-K sensitivity ablation (Phase 4 #1)

Re-runs baseline / HCPC-v1 / CCS-gate / HCPC-v2 across k ∈ {2, 3, 5, 10}. Coherence theory predicts that larger k increases relevance breadth but decreases coherence; if the paradox magnitude scales with k, the theory is empirically supported on a hyperparameter axis reviewers already care about.

## Aggregated metrics

| dataset   |   k | condition   |   n_queries |   faith |   halluc |    sim |   refine_rate |   gate_rate |      ccs |   latency |
|:----------|----:|:------------|------------:|--------:|---------:|-------:|--------------:|------------:|---------:|----------:|
| pubmedqa  |   2 | baseline    |          30 |  0.5986 |   0.1667 | 0.6158 |        0      |      0      | nan      |   11.5087 |
| pubmedqa  |   2 | ccs_gate    |          30 |  0.5721 |   0.1667 | 0.6251 |        0.2667 |      0.2667 |   0.6115 |    8.9783 |
| pubmedqa  |   2 | hcpc_v1     |          30 |  0.5535 |   0.3667 | 0.6391 |        0      |      0      | nan      |    6.8673 |
| pubmedqa  |   2 | hcpc_v2     |          30 |  0.5936 |   0.1333 | 0.6158 |        0      |      0      |   0.6214 |    8.9123 |
| pubmedqa  |   3 | baseline    |          30 |  0.6039 |   0.1333 | 0.5166 |        0      |      0      | nan      |   18.3773 |
| pubmedqa  |   3 | ccs_gate    |          30 |  0.5483 |   0.3333 | 0.538  |        0.9    |      0.9    |   0.2935 |    8.866  |
| pubmedqa  |   3 | hcpc_v1     |          30 |  0.5661 |   0.2667 | 0.5471 |        0      |      0      | nan      |   10.4407 |
| pubmedqa  |   3 | hcpc_v2     |          30 |  0.589  |   0.1333 | 0.5168 |        0.9667 |      0      |   0.3091 |   14.7483 |
| pubmedqa  |   5 | baseline    |          30 |  0.5856 |   0.1667 | 0.4101 |        0      |      0      | nan      |   17.4553 |
| pubmedqa  |   5 | ccs_gate    |          30 |  0.5636 |   0.2333 | 0.4408 |        1      |      1      |   0.1779 |    7.9727 |
| pubmedqa  |   5 | hcpc_v1     |          30 |  0.5608 |   0.2667 | 0.4408 |        0      |      0      | nan      |    9.6547 |
| pubmedqa  |   5 | hcpc_v2     |          30 |  0.5888 |   0.2333 | 0.4463 |        1      |      0      |   0.2072 |   14.7373 |
| pubmedqa  |  10 | baseline    |          30 |  0.5852 |   0.2333 | 0.3082 |        0      |      0      | nan      |   21.0403 |
| pubmedqa  |  10 | ccs_gate    |          30 |  0.5899 |   0.2    | 0.344  |        1      |      1      |   0.1332 |    5.0397 |
| pubmedqa  |  10 | hcpc_v1     |          30 |  0.5863 |   0.1667 | 0.344  |        0      |      0      | nan      |    8.8913 |
| pubmedqa  |  10 | hcpc_v2     |          30 |  0.5789 |   0.2    | 0.4463 |        1      |      0      |   0.2072 |   10.831  |
| squad     |   2 | baseline    |          30 |  0.768  |   0.1    | 0.606  |        0      |      0      | nan      |    3.0763 |
| squad     |   2 | ccs_gate    |          30 |  0.7713 |   0.0667 | 0.6105 |        0.0667 |      0.0667 |   0.6185 |    3.3347 |
| squad     |   2 | hcpc_v1     |          30 |  0.7047 |   0.0667 | 0.6139 |        0      |      0      | nan      |    2.6063 |
| squad     |   2 | hcpc_v2     |          30 |  0.7671 |   0.1    | 0.606  |        0      |      0      |   0.6088 |    1.3903 |
| squad     |   3 | baseline    |          30 |  0.7899 |   0      | 0.5877 |        0      |      0      | nan      |    4.7777 |
| squad     |   3 | ccs_gate    |          30 |  0.7923 |   0      | 0.5943 |        0.2333 |      0.2333 |   0.5388 |    4.6753 |
| squad     |   3 | hcpc_v1     |          30 |  0.721  |   0.1    | 0.6008 |        0      |      0      | nan      |    3.719  |
| squad     |   3 | hcpc_v2     |          30 |  0.7934 |   0      | 0.5879 |        0.5333 |      0      |   0.5425 |    2.794  |
| squad     |   5 | baseline    |          30 |  0.8283 |   0.0333 | 0.5596 |        0      |      0      | nan      |    7.3297 |
| squad     |   5 | ccs_gate    |          30 |  0.7466 |   0      | 0.5714 |        0.7    |      0.7    |   0.4377 |    4.9223 |
| squad     |   5 | hcpc_v1     |          30 |  0.7047 |   0.1333 | 0.5745 |        0      |      0      | nan      |    6.082  |
| squad     |   5 | hcpc_v2     |          30 |  0.8436 |   0      | 0.5629 |        0.9    |      0      |   0.4663 |    6.6227 |
| squad     |  10 | baseline    |          30 |  0.8144 |   0.1    | 0.5169 |        0      |      0      | nan      |   12.415  |
| squad     |  10 | ccs_gate    |          30 |  0.7156 |   0.0667 | 0.5388 |        1      |      1      |   0.3404 |    3.2933 |
| squad     |  10 | hcpc_v1     |          30 |  0.6974 |   0.0667 | 0.5388 |        0      |      0      | nan      |    7.741  |
| squad     |  10 | hcpc_v2     |          30 |  0.8177 |   0.0333 | 0.5359 |        1      |      0      |   0.408  |    9.0777 |

## Paradox magnitude by top-k

| dataset   |   k |   faith_base |   faith_v1 |   faith_v2 |   faith_gate |   paradox |   v2_recovery |   gate_recovery |   ccs_baseline |
|:----------|----:|-------------:|-----------:|-----------:|-------------:|----------:|--------------:|----------------:|---------------:|
| pubmedqa  |   2 |       0.5986 |     0.5535 |     0.5936 |       0.5721 |    0.0451 |        0.0401 |          0.0186 |            nan |
| pubmedqa  |   3 |       0.6039 |     0.5661 |     0.589  |       0.5483 |    0.0378 |        0.0229 |         -0.0178 |            nan |
| pubmedqa  |   5 |       0.5856 |     0.5608 |     0.5888 |       0.5636 |    0.0248 |        0.028  |          0.0028 |            nan |
| pubmedqa  |  10 |       0.5852 |     0.5863 |     0.5789 |       0.5899 |   -0.0011 |       -0.0074 |          0.0036 |            nan |
| squad     |   2 |       0.768  |     0.7047 |     0.7671 |       0.7713 |    0.0633 |        0.0624 |          0.0666 |            nan |
| squad     |   3 |       0.7899 |     0.721  |     0.7934 |       0.7923 |    0.0689 |        0.0724 |          0.0713 |            nan |
| squad     |   5 |       0.8283 |     0.7047 |     0.8436 |       0.7466 |    0.1236 |        0.1389 |          0.0419 |            nan |
| squad     |  10 |       0.8144 |     0.6974 |     0.8177 |       0.7156 |    0.117  |        0.1203 |          0.0182 |            nan |

Target finding: paradox monotonically increases with k on at least one dataset, OR HCPC-v2 / CCS-gate recovery is stable across k.