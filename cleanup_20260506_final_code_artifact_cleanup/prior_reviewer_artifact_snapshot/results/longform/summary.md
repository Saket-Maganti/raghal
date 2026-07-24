# Long-form generation eval (Phase 2 Item 3)

Answers the reviewer question: *does the coherence paradox generalize beyond short-answer QA to long-form generation?*  Runs on QASPER (scientific long-form QA) and MS-MARCO v2.1 (open-domain long-form), measuring both the single-span NLI faithfulness used in the main tables and per-claim NLI faithfulness designed for multi-sentence outputs.

## Aggregated metrics per (dataset, condition)

| dataset   | model   | condition   |   n_queries |   span_faith |   claim_faith |   min_claim_faith |   unsupported_rate |   rouge_l |   mean_answer_tokens |   mean_claims |   halluc_long |   refine_rate |      ccs |   latency |
|:----------|:--------|:------------|------------:|-------------:|--------------:|------------------:|-------------------:|----------:|---------------------:|--------------:|--------------:|--------------:|---------:|----------:|
| msmarco   | mistral | baseline    |          20 |       0.6449 |        0.6462 |            0.5612 |             0.2242 |    0.3189 |                44.4  |          2.05 |          0.4  |          0    | nan      |    2.303  |
| msmarco   | mistral | hcpc_v1     |          20 |       0.6781 |        0.6786 |            0.6166 |             0.075  |    0.323  |                45.95 |          2.15 |          0.05 |          0    | nan      |    2.2305 |
| msmarco   | mistral | hcpc_v2     |          20 |       0.6738 |        0.6736 |            0.6219 |             0.1583 |    0.3054 |                40    |          2    |          0.25 |          0.05 |   0.6762 |    1.9885 |
| qasper    | mistral | baseline    |          20 |       0.649  |        0.649  |            0.5471 |             0.1583 |    0.0794 |                48.5  |          2.45 |          0.3  |          0    | nan      |    6.5955 |
| qasper    | mistral | hcpc_v1     |          20 |       0.6471 |        0.6471 |            0.5669 |             0.1167 |    0.0869 |                41.9  |          2.1  |          0.2  |          0    | nan      |    1.718  |
| qasper    | mistral | hcpc_v2     |          20 |       0.6483 |        0.6506 |            0.5624 |             0.1292 |    0.0786 |                49.25 |          2.45 |          0.25 |          0.7  |   0.4444 |    2.2315 |

## Paradox magnitude on long-form outputs

`span_*` columns reuse the single-span NLI metric for backward comparability.  `claim_*` columns use the per-sentence aggregation.  A paradox that appears on *both* is stronger evidence than one that appears only on the coarse span metric.

| dataset   | model   |   span_faith_base |   span_faith_v1 |   span_faith_v2 |   span_paradox_drop |   span_v2_recovery |   claim_faith_base |   claim_faith_v1 |   claim_faith_v2 |   claim_paradox_drop |   claim_v2_recovery |   rouge_l_base |   rouge_l_v1 |   rouge_l_v2 |   unsupported_rate_base |   unsupported_rate_v1 |   unsupported_rate_v2 |
|:----------|:--------|------------------:|----------------:|----------------:|--------------------:|-------------------:|-------------------:|-----------------:|-----------------:|---------------------:|--------------------:|---------------:|-------------:|-------------:|------------------------:|----------------------:|----------------------:|
| msmarco   | mistral |            0.6449 |          0.6781 |          0.6738 |             -0.0332 |            -0.0043 |             0.6462 |           0.6786 |           0.6736 |              -0.0324 |             -0.005  |         0.3189 |       0.323  |       0.3054 |                  0.2242 |                0.075  |                0.1583 |
| qasper    | mistral |            0.649  |          0.6471 |          0.6483 |              0.0019 |             0.0012 |             0.649  |           0.6471 |           0.6506 |               0.0019 |              0.0035 |         0.0794 |       0.0869 |       0.0786 |                  0.1583 |                0.1167 |                0.1292 |

## Interpretation targets

1. `claim_paradox_drop > 0` on at least one dataset → paradox generalizes to long-form.  
2. `claim_v2_recovery ≥ 0` on every dataset → v2 remains a net win under the claim-level aggregation.  
3. `rouge_l_v2 ≥ rouge_l_baseline` → v2 does not sacrifice answer-quality vs the gold reference while improving faithfulness.