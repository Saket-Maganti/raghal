# Multi-seed variance (Item 5 — reviewer error bars)

`faith_std` and `halluc_std` are std-of-seed-means (not std of raw queries).
`significant_drop` ≈ |paradox_drop| > 2·σ (≈ p<0.05 single-tail).

## Per-condition variance

| dataset   | condition   |   n_seeds |   faith_mean |   faith_std |   halluc_mean |   halluc_std |   refine_mean |
|:----------|:------------|----------:|-------------:|------------:|--------------:|-------------:|--------------:|
| pubmedqa  | baseline    |         3 |       0.5987 |      0.0019 |        0.1333 |       0      |        0      |
| pubmedqa  | hcpc_v1     |         3 |       0.5556 |      0.013  |        0.3333 |       0.0667 |        0      |
| pubmedqa  | hcpc_v2     |         3 |       0.5995 |      0.0036 |        0.1556 |       0.0192 |        0.9667 |
| squad     | baseline    |         3 |       0.7913 |      0.0014 |        0      |       0      |        0      |
| squad     | hcpc_v1     |         3 |       0.722  |      0.0037 |        0.1111 |       0.0192 |        0      |
| squad     | hcpc_v2     |         3 |       0.7927 |      0.0024 |        0      |       0      |        0.5333 |

## Coherence paradox with error bars

| dataset   |   paradox_drop |   paradox_drop_std |   v2_recovery |   v2_recovery_std | significant_drop   |
|:----------|---------------:|-------------------:|--------------:|------------------:|:-------------------|
| pubmedqa  |         0.0431 |             0.0131 |        0.0439 |            0.0135 | True               |
| squad     |         0.0693 |             0.004  |        0.0707 |            0.0044 | True               |
