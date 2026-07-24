# Noise-injection ablation (NeurIPS Gap 1)

Replaces {0, 1, 2, K} of K retrieved passages with random off-topic
passages from the same corpus to disentangle the coherence paradox
from generic retrieval noise.

## Aggregated faithfulness vs noise rate

| dataset   | model   |   n_noise |   noise_rate |   n_queries |   faith_mean |   faith_std |   halluc_mean |
|:----------|:--------|----------:|-------------:|------------:|-------------:|------------:|--------------:|
| hotpotqa  | mistral |         0 |        0     |          30 |       0.6043 |      0.112  |        0.2333 |
| hotpotqa  | mistral |         1 |        0.333 |          30 |       0.5898 |      0.0911 |        0.2    |
| hotpotqa  | mistral |         2 |        0.667 |          30 |       0.6402 |      0.1018 |        0.1    |
| hotpotqa  | mistral |         3 |        1     |          30 |       0.6321 |      0.0957 |        0.1    |
| pubmedqa  | mistral |         0 |        0     |          30 |       0.5931 |      0.1252 |        0.1667 |
| pubmedqa  | mistral |         1 |        0.333 |          30 |       0.5921 |      0.1171 |        0.2    |
| pubmedqa  | mistral |         2 |        0.667 |          30 |       0.566  |      0.1084 |        0.3333 |
| pubmedqa  | mistral |         3 |        1     |          30 |       0.6302 |      0.0782 |        0.0667 |
| squad     | mistral |         0 |        0     |          30 |       0.7902 |      0.1548 |        0      |
| squad     | mistral |         1 |        0.333 |          30 |       0.7731 |      0.1552 |        0.0333 |
| squad     | mistral |         2 |        0.667 |          30 |       0.723  |      0.1438 |        0.0333 |
| squad     | mistral |         3 |        1     |          30 |       0.6355 |      0.1092 |        0.1    |

## Coherence paradox vs noise sensitivity

`noise_slope` = linear regression slope of faithfulness on noise_rate.  
`paradox_drop` = faith_baseline − faith_v1 from the multidataset run.  
`paradox_vs_noise_ratio` >= 2 supports the claim that the coherence
paradox is a *distinct failure mode* not explainable by generic noise.

| dataset   | model   |   faith@noise0 |   faith@noise1 |   noise_drop |   noise_slope |   paradox_drop |   paradox_vs_noise_ratio |
|:----------|:--------|---------------:|---------------:|-------------:|--------------:|---------------:|-------------------------:|
| hotpotqa  | mistral |         0.6043 |         0.6321 |      -0.0278 |        0.0402 |        -0.0104 |                    -0.26 |
| pubmedqa  | mistral |         0.5931 |         0.6302 |      -0.0371 |        0.0255 |         0.0247 |                     0.97 |
| squad     | mistral |         0.7902 |         0.6355 |       0.1547 |       -0.1542 |         0.0999 |                     0.65 |

A ratio ≥ 2 across all datasets is the target finding.