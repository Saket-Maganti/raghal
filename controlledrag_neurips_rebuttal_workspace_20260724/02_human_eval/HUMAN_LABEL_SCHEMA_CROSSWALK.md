# Human Label Schema Crosswalk

## Non-pooling rule

The `n=99` typical slice and `n=100` disagreement-targeted slice have
different sampling designs and label schemas. They are analyzed separately.
This crosswalk explains interpretation only; it does not authorize pooling,
row concatenation, or a joint prevalence estimate.

| Concept | `n=99` typical slice | `n=100` disagreement-targeted slice |
| --- | --- | --- |
| Pre-adjudication rater fields | `rater_a_label`, `rater_b_label` | `human_label_rater1`, `human_label_rater2` |
| Adjudicated field | `adjudicated_label` | `adjudicated_label` |
| Positive/support label | `supported` | `faithful` |
| Intermediate label | `partially_supported` | `unclear` |
| Negative/unsupported label | `unsupported` | `hallucinated` |
| Primary alignment endpoint | ordinal: `0`, `0.5`, `1` | ordinal correlations; binary AUROC/AP |
| Locked binary endpoint | not defined for all 99 rows | `faithful=1`, `hallucinated=0`; no adjudicated `unclear` rows |
| Sampling role | typical calibration | deliberately targeted scorer disagreement |

## Permitted numeric mappings

For `n=99` correlation checks:

- `unsupported=0`;
- `partially_supported=0.5`;
- `supported=1`.

AUROC and average precision are not primary metrics for this three-level
endpoint. Prompt 03 supplies a secondary sensitivity restricted to the 83
determinate rows (`supported=1`, `unsupported=0`), excluding all 16
`partially_supported` rows. It must be labeled secondary and should not be
used as a headline result because only four negative rows remain.

For `n=100`:

- ordinal correlations use `hallucinated=0`, `unclear=0.5`, `faithful=1`;
- submitted AUROC and average precision use `faithful=1`,
  `hallucinated=0`, with `unclear` treated as missing;
- there are no `unclear` adjudicated labels, so all 100 rows enter the locked
  binary metrics.

## Agreement rule

Raw agreement and unweighted Cohen's kappa use the two independent
pre-adjudication label columns. Scorer alignment uses the final adjudicated
label. Adjudicated labels must never be substituted into agreement
calculations.
