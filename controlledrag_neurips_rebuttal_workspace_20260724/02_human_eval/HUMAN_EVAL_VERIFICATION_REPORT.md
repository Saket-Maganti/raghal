# Human-Evaluation Verification Report

## Status

`VERIFIED_SEPARATELY_WITH_BOUNDED_BINARY_SENSITIVITY`

Both human-evaluation panels have the expected row counts, unique IDs, and
complete load-bearing label/score fields. Submitted alignment point estimates
reproduce from fixed data. The panels remain separate throughout.

## Structural verification

| Panel | Rows | Unique IDs | Duplicate IDs | Missing essential cells | Conditions |
| --- | ---: | ---: | ---: | ---: | --- |
| Typical | 99 | 99 | 0 | 0 | 33 baseline / 33 HCPC-v1 / 33 HCPC-v2 |
| Disagreement-targeted | 100 | 100 | 0 | 0 | 34 baseline / 33 HCPC-v1 / 33 HCPC-v2 |

The `n=100` `example_id` and `query_id` fields are both unique. The `n=99`
adjudication IDs match the recovered fixed scorer-template IDs exactly.

## Pre-adjudication agreement

| Panel | Disagreements | Raw agreement (95% bootstrap CI) | Unweighted kappa (95% bootstrap CI) |
| --- | ---: | ---: | ---: |
| `n=99` | 8 | 0.919 (0.859, 0.970) | 0.774 (0.613, 0.906) |
| `n=100` | 12 | 0.880 (0.820, 0.940) | 0.721 (0.596, 0.845) |

Prompt 03 intervals use 10,000 row-bootstrap resamples with recorded seeds.
The submitted `n=100` 1,000-resample intervals also reproduce the same point
estimates.

## Label distributions

For `n=99`, rater A labeled `75/20/4` rows
supported/partially-supported/unsupported; rater B labeled `80/14/5`; the
adjudicated distribution is `79/16/4`.

For `n=100`, rater 1 labeled `74/26` faithful/hallucinated; rater 2 labeled
`70/20/10` faithful/hallucinated/unclear; the adjudicated distribution is
`74/26/0`.

These are slice descriptions, not population prevalence estimates.

## Scorer-to-human alignment

Spearman correlations against adjudicated ordinal labels:

| Panel | Legacy DeBERTa proxy | Second NLI proxy | RAGAS-style judge |
| --- | ---: | ---: | ---: |
| `n=99` | 0.103 (-0.084, 0.279) | 0.394 (0.223, 0.541) | 0.549 (0.375, 0.711) |
| `n=100` | -0.156 (-0.331, 0.032) | 0.446 (0.293, 0.581) | 0.384 (0.241, 0.523) |

The `n=99` intervals are the submitted fixed-output 10,000-resample
intervals. The `n=100` intervals are the submitted fixed-output
1,000-resample intervals.

Paired 10,000-resample differences show that, on `n=99`, the RAGAS-style
judge exceeds the second proxy by 0.155 (0.017, 0.314). On the targeted
`n=100` slice, the second proxy versus RAGAS-style difference is not resolved:
RAGAS minus second is -0.062 (-0.234, 0.116). This is evidence of
slice-dependent ranking, not a universal best scorer.

## AUROC and locked average precision

The primary submitted binary metrics apply to `n=100` only:

| Scorer | AUROC (95% CI) | Average precision (95% CI) |
| --- | ---: | ---: |
| Legacy DeBERTa proxy | 0.398 (0.273, 0.514) | 0.765 (0.670, 0.852) |
| Second NLI proxy | 0.794 (0.699, 0.879) | 0.929 (0.881, 0.963) |
| RAGAS-style judge | 0.718 (0.637, 0.793) | 0.859 (0.793, 0.914) |

Average precision is locked to
`sklearn.metrics.average_precision_score`, with `faithful=1`, higher scorer
values indicating greater faithfulness, and no score inversion.

The `n=99` primary endpoint is ordinal, so an all-row AUROC/AP is not defined
without inventing a binary collapse. A secondary 83-row determinate-only
sensitivity is provided in `HUMAN_EVAL_SAFE_NUMBERS.csv`; it excludes 16
partially-supported rows and retains only four negative examples. Its high
average-precision values are therefore strongly base-rate-sensitive and are
not suitable headline evidence.

## Reproduction surface

The executable audit is
`03_existing_analyses/scripts/analyze_prompt03_existing_outputs.py`. Its
input hashes, runtime versions, and derived tables are recorded under
`03_existing_analyses/results/`. It performs no model inference or network
access.
