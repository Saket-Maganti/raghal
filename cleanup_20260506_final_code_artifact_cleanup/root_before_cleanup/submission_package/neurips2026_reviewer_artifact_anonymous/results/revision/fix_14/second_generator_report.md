# Fix 14 - second-generator metric-fragility replication

Generator: `qwen2.5` via local Ollama. Sample target: 100 rows per condition.
No paid APIs are used.

## Metric means and effect sizes

| generator_model   | metric           |   n_baseline |   n_hcpc_v1 |   n_hcpc_v2 |   faith_baseline |   faith_hcpc_v1 |   faith_hcpc_v2 |   paradox_drop_baseline_minus_v1 |   v2_recovery_v2_minus_v1 |
|:------------------|:-----------------|-------------:|------------:|------------:|-----------------:|----------------:|----------------:|---------------------------------:|--------------------------:|
| qwen2.5           | faith_deberta    |          100 |         100 |         100 |         0.645209 |        0.630625 |        0.64426  |                         0.014584 |                  0.013635 |
| qwen2.5           | faith_second_nli |          100 |         100 |         100 |         0.361836 |        0.316289 |        0.367532 |                         0.045547 |                  0.051243 |
| qwen2.5           | faith_ragas      |          100 |         100 |         100 |         0.806    |        0.672    |        0.814    |                         0.134    |                  0.142    |

## Metric correlations

| metric_a         | metric_b         |   n |   pearson_r |   pearson_p |   spearman_rho |   spearman_p |
|:-----------------|:-----------------|----:|------------:|------------:|---------------:|-------------:|
| faith_deberta    | faith_second_nli | 300 |    0.379549 | 1.02617e-11 |       0.428603 |  7.79391e-15 |
| faith_deberta    | faith_ragas      | 300 |    0.28012  | 8.1967e-07  |       0.317759 |  1.83075e-08 |
| faith_second_nli | faith_ragas      | 300 |    0.721134 | 2.02021e-49 |       0.667552 |  4.62186e-40 |

## Compact interpretation

If scorer disagreement persists here, it reduces the concern that the main metric-fragility result is purely Mistral-specific.
If it does not persist, generator identity should be treated as another required audit axis.
