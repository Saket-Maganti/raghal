# RAPTOR head-to-head (Phase 2 Item 1)

Compared conditions: `baseline`, `hcpc_v1`, `hcpc_v2`, `raptor`.
RAPTOR config: 2-level tree, n_clusters=6, mix_ratio=0.5 (≥1 summary slot, rest leaves).

## Aggregated metrics

| dataset   | model   | condition   |   n_queries |   faith |   halluc |    sim |   refine_rate |   mean_summaries |   mean_leaves |
|:----------|:--------|:------------|------------:|--------:|---------:|-------:|--------------:|-----------------:|--------------:|
| hotpotqa  | mistral | baseline    |          30 |  0.6107 |   0.2333 | 0.552  |        0      |                0 |             0 |
| hotpotqa  | mistral | hcpc_v1     |          30 |  0.6368 |   0.1333 | 0.5699 |        0      |                0 |             0 |
| hotpotqa  | mistral | hcpc_v2     |          30 |  0.6156 |   0.1667 | 0.5519 |        0.5667 |                0 |             0 |
| hotpotqa  | mistral | raptor      |          30 |  0.5835 |   0.2333 | 0.4756 |        1      |                1 |             2 |
| pubmedqa  | mistral | baseline    |          30 |  0.6058 |   0.1333 | 0.5166 |        0      |                0 |             0 |
| pubmedqa  | mistral | hcpc_v1     |          30 |  0.5546 |   0.2333 | 0.5471 |        0      |                0 |             0 |
| pubmedqa  | mistral | hcpc_v2     |          30 |  0.5963 |   0.2333 | 0.5168 |        0.9667 |                0 |             0 |
| pubmedqa  | mistral | raptor      |          30 |  0.5906 |   0.2333 | 0.5188 |        1      |                1 |             2 |
| squad     | mistral | baseline    |          30 |  0.787  |   0      | 0.5877 |        0      |                0 |             0 |
| squad     | mistral | hcpc_v1     |          30 |  0.7102 |   0.1667 | 0.6008 |        0      |                0 |             0 |
| squad     | mistral | hcpc_v2     |          30 |  0.7991 |   0      | 0.5879 |        0.5333 |                0 |             0 |
| squad     | mistral | raptor      |          30 |  0.7911 |   0.0333 | 0.6008 |        1      |                1 |             2 |

## RAPTOR vs HCPC deltas

Positive `raptor_vs_v*_faith` = RAPTOR wins on faithfulness.
Negative `raptor_vs_v*_halluc` = RAPTOR has fewer hallucinations.

| dataset   | model   |   faith_baseline |   faith_v1 |   faith_v2 |   faith_raptor |   halluc_baseline |   halluc_v1 |   halluc_v2 |   halluc_raptor |   raptor_vs_v1_faith |   raptor_vs_v2_faith |   raptor_vs_v1_halluc |   raptor_vs_v2_halluc |
|:----------|:--------|-----------------:|-----------:|-----------:|---------------:|------------------:|------------:|------------:|----------------:|---------------------:|---------------------:|----------------------:|----------------------:|
| hotpotqa  | mistral |           0.6107 |     0.6368 |     0.6156 |         0.5835 |            0.2333 |      0.1333 |      0.1667 |          0.2333 |              -0.0533 |              -0.0321 |                0.1    |                0.0666 |
| pubmedqa  | mistral |           0.6058 |     0.5546 |     0.5963 |         0.5906 |            0.1333 |      0.2333 |      0.2333 |          0.2333 |               0.036  |              -0.0057 |                0      |                0      |
| squad     | mistral |           0.787  |     0.7102 |     0.7991 |         0.7911 |            0      |      0.1667 |      0      |          0.0333 |               0.0809 |              -0.008  |               -0.1334 |                0.0333 |
