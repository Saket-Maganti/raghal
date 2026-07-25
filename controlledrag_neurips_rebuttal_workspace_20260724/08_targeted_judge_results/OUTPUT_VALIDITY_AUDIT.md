# Output validity audit

| Quantity | Independent result |
| --- | ---: |
| requested | 1,510 |
| received | 1,510 |
| strictly valid | 1,507 |
| invalid | 3 |
| valid-output rate | 0.9980132450 |
| missing keys | 0 |
| duplicate keys | 0 |
| unexpected keys | 0 |
| model or revision errors | 0 |
| validator disagreements | 0 |
| parsed-payload disagreements | 0 |
| maximum differential missingness | 0.0078125 |

Invalid category:

```text
threshold_inconsistency = 3
```

All three objects have score 50 with a false Boolean faithful decision. The frozen rule is score `>= 50` implies faithful `true`. The objects remain invalid and preserved.

Inclusion checks:

- valid rate is at least 98%;
- differential missingness is no more than two percentage points;
- no keys are missing, duplicated, or unexpected;
- model and manifests are verified.

Classification: `STRONG_INCLUSION_GATE_PASS`.
