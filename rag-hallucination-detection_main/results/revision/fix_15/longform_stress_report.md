# Fix 15 - long-form/synthesis stress test

Source: existing `results/longform/` run, 40 distinct long-form questions.
This is exploratory appendix evidence only; it is not a broad long-form validation.

## Aggregated condition metrics

| dataset   | model   | condition   |   n_queries |   span_faith |   claim_faith |   unsupported_rate |   rouge_l |   halluc_long |   refine_rate |      ccs | source                       |   span_paradox_drop |   claim_paradox_drop |   unsupported_rate_base |   unsupported_rate_v1 |   unsupported_rate_v2 |
|:----------|:--------|:------------|------------:|-------------:|--------------:|-------------------:|----------:|--------------:|--------------:|---------:|:-----------------------------|--------------------:|---------------------:|------------------------:|----------------------:|----------------------:|
| msmarco   | mistral | baseline    |          20 |       0.6449 |        0.6462 |             0.2242 |    0.3189 |          0.4  |          0    | nan      | results/longform/summary.csv |                 nan |                  nan |                     nan |                   nan |                   nan |
| msmarco   | mistral | hcpc_v1     |          20 |       0.6781 |        0.6786 |             0.075  |    0.323  |          0.05 |          0    | nan      | results/longform/summary.csv |                 nan |                  nan |                     nan |                   nan |                   nan |
| msmarco   | mistral | hcpc_v2     |          20 |       0.6738 |        0.6736 |             0.1583 |    0.3054 |          0.25 |          0.05 |   0.6762 | results/longform/summary.csv |                 nan |                  nan |                     nan |                   nan |                   nan |
| qasper    | mistral | baseline    |          20 |       0.649  |        0.649  |             0.1583 |    0.0794 |          0.3  |          0    | nan      | results/longform/summary.csv |                 nan |                  nan |                     nan |                   nan |                   nan |
| qasper    | mistral | hcpc_v1     |          20 |       0.6471 |        0.6471 |             0.1167 |    0.0869 |          0.2  |          0    | nan      | results/longform/summary.csv |                 nan |                  nan |                     nan |                   nan |                   nan |
| qasper    | mistral | hcpc_v2     |          20 |       0.6483 |        0.6506 |             0.1292 |    0.0786 |          0.25 |          0.7  |   0.4444 | results/longform/summary.csv |                 nan |                  nan |                     nan |                   nan |                   nan |

## Contrast rows

| dataset   | model   | condition   |   n_queries |   span_faith |   claim_faith |   unsupported_rate |   rouge_l |   halluc_long |   refine_rate |   ccs | source                                |   span_paradox_drop |   claim_paradox_drop |   unsupported_rate_base |   unsupported_rate_v1 |   unsupported_rate_v2 |
|:----------|:--------|:------------|------------:|-------------:|--------------:|-------------------:|----------:|--------------:|--------------:|------:|:--------------------------------------|--------------------:|---------------------:|------------------------:|----------------------:|----------------------:|
| msmarco   | mistral | contrast    |         nan |          nan |           nan |                nan |       nan |           nan |           nan |   nan | results/longform/paradox_longform.csv |             -0.0332 |              -0.0324 |                  0.2242 |                0.075  |                0.1583 |
| qasper    | mistral | contrast    |         nan |          nan |           nan |                nan |       nan |           nan |           nan |   nan | results/longform/paradox_longform.csv |              0.0019 |               0.0019 |                  0.1583 |                0.1167 |                0.1292 |

## Compact interpretation

The small stress test shows that scorer and condition sensitivity can appear outside short-answer QA, but the sample is too small and dataset-specific for broad claims.
It belongs in the supplement as a scope probe, not as a central result.
