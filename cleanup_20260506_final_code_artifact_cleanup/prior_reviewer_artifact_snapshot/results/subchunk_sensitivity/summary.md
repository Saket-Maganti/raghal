# HCPC-v2 sub-chunk sensitivity (Upgrade Item 7)

Sweeping the internal sub-chunk size over {128, 256, 512} tokens to test whether the coherence paradox and v2 recovery depend on this hyperparameter.

## Aggregated metrics

| dataset   |   sub_chunk | condition   |   n_queries |   faith |   halluc |    sim |   refine_rate |      ccs |
|:----------|------------:|:------------|------------:|--------:|---------:|-------:|--------------:|---------:|
| pubmedqa  |         128 | baseline    |          30 |  0.6198 |   0.1    | 0.5166 |        0      | nan      |
| pubmedqa  |         128 | hcpc_v1     |          30 |  0.5675 |   0.2    | 0.5482 |        0      | nan      |
| pubmedqa  |         128 | hcpc_v2     |          30 |  0.6029 |   0.1667 | 0.5154 |        0.9667 |   0.3068 |
| pubmedqa  |         256 | baseline    |          30 |  0.6007 |   0.1667 | 0.5166 |        0      | nan      |
| pubmedqa  |         256 | hcpc_v1     |          30 |  0.5505 |   0.3    | 0.5471 |        0      | nan      |
| pubmedqa  |         256 | hcpc_v2     |          30 |  0.5959 |   0.1667 | 0.5168 |        0.9667 |   0.3091 |
| pubmedqa  |         512 | baseline    |          30 |  0.5938 |   0.2    | 0.5166 |        0      | nan      |
| pubmedqa  |         512 | hcpc_v1     |          30 |  0.5758 |   0.2    | 0.5372 |        0      | nan      |
| pubmedqa  |         512 | hcpc_v2     |          30 |  0.5961 |   0.2    | 0.5163 |        0.9667 |   0.3092 |
| squad     |         128 | baseline    |          30 |  0.7882 |   0      | 0.5877 |        0      | nan      |
| squad     |         128 | hcpc_v1     |          30 |  0.7237 |   0      | 0.6075 |        0      | nan      |
| squad     |         128 | hcpc_v2     |          30 |  0.7885 |   0      | 0.5893 |        0.5333 |   0.5433 |
| squad     |         256 | baseline    |          30 |  0.8013 |   0      | 0.5877 |        0      | nan      |
| squad     |         256 | hcpc_v1     |          30 |  0.7014 |   0.1    | 0.6008 |        0      | nan      |
| squad     |         256 | hcpc_v2     |          30 |  0.781  |   0      | 0.5879 |        0.5333 |   0.5425 |
| squad     |         512 | baseline    |          30 |  0.7972 |   0.0333 | 0.5877 |        0      | nan      |
| squad     |         512 | hcpc_v1     |          30 |  0.7696 |   0.0333 | 0.6039 |        0      | nan      |
| squad     |         512 | hcpc_v2     |          30 |  0.7909 |   0      | 0.5874 |        0.5333 |   0.5428 |

## Paradox magnitude per sub-chunk setting

`paradox_drop` = faith_baseline − faith_v1 (positive = paradox confirmed).  
`v2_recovery` = faith_v2 − faith_v1 (positive = v2 helps).

| dataset   |   sub_chunk |   faith_base |   faith_v1 |   faith_v2 |   paradox_drop |   v2_recovery |   halluc_base |   halluc_v2 |   refine_rate |
|:----------|------------:|-------------:|-----------:|-----------:|---------------:|--------------:|--------------:|------------:|--------------:|
| pubmedqa  |         128 |       0.6198 |     0.5675 |     0.6029 |         0.0523 |        0.0354 |        0.1    |      0.1667 |        0.9667 |
| pubmedqa  |         256 |       0.6007 |     0.5505 |     0.5959 |         0.0502 |        0.0454 |        0.1667 |      0.1667 |        0.9667 |
| pubmedqa  |         512 |       0.5938 |     0.5758 |     0.5961 |         0.018  |        0.0203 |        0.2    |      0.2    |        0.9667 |
| squad     |         128 |       0.7882 |     0.7237 |     0.7885 |         0.0645 |        0.0648 |        0      |      0      |        0.5333 |
| squad     |         256 |       0.8013 |     0.7014 |     0.781  |         0.0999 |        0.0796 |        0      |      0      |        0.5333 |
| squad     |         512 |       0.7972 |     0.7696 |     0.7909 |         0.0276 |        0.0213 |        0.0333 |      0      |        0.5333 |

A stable paradox magnitude (±0.02 faith points) across sub-chunk settings indicates the effect is structural, not tuned.