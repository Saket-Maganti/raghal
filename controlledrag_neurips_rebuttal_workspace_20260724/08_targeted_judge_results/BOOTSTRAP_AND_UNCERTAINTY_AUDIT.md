# Bootstrap and uncertainty audit

Primary plan:

```text
seed = 20260724
replicates = 10000
interval = percentile 95%
point estimate = direct observed statistic
```

| Analysis | Finite replicates |
| --- | ---: |
| answer-only main contrast | 10,000 |
| context-conditioned main contrast | 10,000 |
| difference in contrasts | 10,000 |
| typical AP difference | 9,822 |
| typical Spearman difference | 9,822 |
| diagnostic AP difference | 10,000 |
| diagnostic Spearman difference | 9,991 |

Samples with only one human class make AP undefined; constant score or label arrays can make Spearman undefined. Only those non-finite statistics are omitted from the corresponding CI distribution.

The generated package's seed offsets are not carried into final Prompt B tables.
