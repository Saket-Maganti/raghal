# Confidence calibration (Phase 5 #9)

Backend: ollama, Model: mistral, n=60

## Correlations

| dataset   |   n |   pearson_r |   pearson_p |   spearman_rho |   spearman_p |
|:----------|----:|------------:|------------:|---------------:|-------------:|
| __all__   |  60 |      0.36   |      0.0047 |         0.4815 |       0.0001 |
| pubmedqa  |  30 |      0.0664 |      0.7273 |         0.0323 |       0.8654 |
| squad     |  30 |      0.2563 |      0.1716 |         0.1295 |       0.4953 |

## Joint quintile breakdown

|   quintile |   ccs_mean |   ccs_halluc_rate |   ccs_n |   conf_mean |   conf_halluc_rate |   conf_n |
|-----------:|-----------:|------------------:|--------:|------------:|-------------------:|---------:|
|          1 |      0.167 |            0.3333 |      12 |         5.8 |             0.1667 |       12 |
|          2 |      0.328 |            0.1667 |      12 |        67.7 |             0.25   |       12 |
|          3 |      0.459 |            0      |      12 |        99.7 |             0.0833 |       36 |
|          4 |      0.554 |            0      |      14 |       nan   |           nan      |        0 |
|          5 |      0.635 |            0.2    |      10 |       nan   |           nan      |        0 |

Reading: if pearson_r > 0.3 with p < 0.05, the model's self-reported confidence aligns with CCS — the LLM implicitly tracks coherence.