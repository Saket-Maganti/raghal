# Independent statistical recomputation

The private recomputation reads only frozen manifests, raw accepted-run records, the strict schema, and model/repair receipts. It does not consume the package's generated analysis CSVs.

## Main fixed-output contrasts

| Interface | n pairs | Baseline mean | HCPC-v1 mean | Baseline minus HCPC-v1 | 95% percentile CI |
| --- | ---: | ---: | ---: | ---: | ---: |
| answer-only | 193 | 8.75648 | 5.44041 | 3.31606 | [0.46632, 6.26943] |
| context-conditioned | 193 | 37.35751 | 23.41969 | 13.93782 | [9.53368, 18.23834] |

Difference in contrasts, context-conditioned minus answer-only:

```text
10.6217616580
95% CI [5.5440414508, 15.4922279793]
```

Both system contrasts are positive. The result is `same sign / material magnitude change`.

## Typical human slice

| Metric | Answer-only | Context-conditioned |
| --- | ---: | ---: |
| AP | 0.962788 | 0.981699 |
| Spearman | 0.117791 | 0.250745 |
| Boolean accuracy | 0.265060 | 0.602410 |
| Balanced accuracy | 0.613924 | 0.791139 |
| F1 | 0.371134 | 0.736000 |
| Brier | 0.778343 | 0.486657 |

Direct context-minus-answer differences:

- AP `+0.0189111`, CI `[0.0044079, 0.0421687]`, 9,822 finite replicates;
- Spearman `+0.1329539`, CI `[0.0607211, 0.2150563]`, 9,822 finite replicates.

## Disagreement-targeted diagnostic slice

| Metric | Answer-only | Context-conditioned |
| --- | ---: | ---: |
| AP | 0.798559 | 0.864252 |
| Spearman | 0.052908 | 0.299195 |
| Boolean accuracy | 0.277778 | 0.500000 |
| Balanced accuracy | 0.519298 | 0.659649 |
| F1 | 0.187500 | 0.550000 |
| Brier | 0.732639 | 0.534861 |

Direct context-minus-answer differences:

- AP `+0.0656936`, CI `[0.0163048, 0.1193325]`, 10,000 finite replicates;
- Spearman `+0.2462864`, CI `[0.0234176, 0.5062600]`, 9,991 finite replicates.

All intervals use seed `20260724`, 10,000 resamples, and the documented pairing unit.
