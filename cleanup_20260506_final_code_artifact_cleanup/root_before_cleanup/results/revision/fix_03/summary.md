# Fix 3 - multi-metric faithfulness

## Condition Means

| dataset   | condition   |    n |   deberta |   second_nli |    ragas |
|:----------|:------------|-----:|----------:|-------------:|---------:|
| squad     | baseline    | 2500 |  0.660947 |     0.350109 | 0.72964  |
| squad     | hcpc_v1     | 2500 |  0.650271 |     0.318418 | 0.590434 |
| squad     | hcpc_v2     | 2500 |  0.661196 |     0.350878 | 0.727948 |

## Metric Correlations

| metric_a         | metric_b         |    n |   pearson_r |   pearson_p |   spearman_rho |   spearman_p |
|:-----------------|:-----------------|-----:|------------:|------------:|---------------:|-------------:|
| faith_deberta    | faith_second_nli | 7500 |    0.258666 | 6.2756e-115 |       0.265295 | 5.18018e-121 |
| faith_deberta    | faith_ragas      | 7500 |    0.181871 | 8.64758e-57 |       0.212055 | 5.3135e-77   |
| faith_second_nli | faith_ragas      | 7500 |    0.674177 | 0           |       0.651497 | 0            |
