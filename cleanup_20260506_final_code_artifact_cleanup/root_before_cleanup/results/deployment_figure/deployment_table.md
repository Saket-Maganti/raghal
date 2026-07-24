# Deployment case study — latency vs faithfulness

Source: existing `per_query.csv` from head-to-head, multidataset, and multi-retriever sweeps. No new runs.

## Per-dataset Pareto frontier (latency↓, faith↑)

### hotpotqa

| condition | n | median_lat (s) | p95_lat (s) | faith | halluc | on_pareto |
|---|---:|---:|---:|---:|---:|:---:|
| crag | 30 | 1.21 | 2.70 | 0.631 | 0.233 | ✅ |
| hcpc_v1 | 30 | 1.46 | 3.02 | 0.650 | 0.167 | ✅ |
| hcpc_v2 | 30 | 1.71 | 3.52 | 0.607 | 0.233 |  |
| baseline | 30 | 1.84 | 3.59 | 0.609 | 0.167 |  |
| selfrag | 30 | 4.63 | 8.07 | 0.551 | 0.433 |  |

### pubmedqa

| condition | n | median_lat (s) | p95_lat (s) | faith | halluc | on_pareto |
|---|---:|---:|---:|---:|---:|:---:|
| crag | 30 | 2.50 | 5.38 | 0.586 | 0.333 | ✅ |
| hcpc_v1 | 150 | 6.07 | 11.27 | 0.570 | 0.233 |  |
| hcpc_v2 | 150 | 8.66 | 15.62 | 0.590 | 0.167 | ✅ |
| baseline | 150 | 10.94 | 16.39 | 0.601 | 0.173 | ✅ |

### squad

| condition | n | median_lat (s) | p95_lat (s) | faith | halluc | on_pareto |
|---|---:|---:|---:|---:|---:|:---:|
| crag | 30 | 1.16 | 2.42 | 0.787 | 0.033 | ✅ |
| hcpc_v1 | 150 | 1.97 | 4.66 | 0.766 | 0.040 |  |
| hcpc_v2 | 150 | 3.15 | 5.97 | 0.808 | 0.013 | ✅ |
| baseline | 150 | 3.81 | 6.78 | 0.799 | 0.027 |  |
| selfrag | 22 | 4.91 | 10.18 | 0.550 | 0.455 |  |

## Deployment takeaway

Picks on the frontier (choose per dataset):

- **hotpotqa**: `hcpc_v1` — 1.46s / faith=0.650 / halluc=0.167
- **hotpotqa**: `crag` — 1.21s / faith=0.631 / halluc=0.233
- **pubmedqa**: `baseline` — 10.94s / faith=0.601 / halluc=0.173
- **pubmedqa**: `hcpc_v2` — 8.66s / faith=0.590 / halluc=0.167
- **pubmedqa**: `crag` — 2.50s / faith=0.586 / halluc=0.333
- **squad**: `hcpc_v2` — 3.15s / faith=0.808 / halluc=0.013
- **squad**: `crag` — 1.16s / faith=0.787 / halluc=0.033
