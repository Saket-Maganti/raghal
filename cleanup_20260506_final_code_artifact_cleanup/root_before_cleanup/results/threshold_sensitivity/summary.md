# HCPC-v2 Threshold Sensitivity Analysis

Mode: retrieval-only (CCS proxy) *(retrieval-only — ranked by proxy_score = 0.4·CCS − 0.3·emb_var − 0.2·entropy + 0.1·qsim)*
Fixed grid: sim=[0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6], ce=[-0.3, -0.25, -0.2, -0.15, -0.1, -0.05], topk_protected=[0, 1, 2, 3]
Adaptive configs: [(60, 40), (50, 50), (70, 30), (60, 30)]

## SQUAD

### Fixed thresholds — top-10 by proxy_score

| Config ID | sim | ce | topk_prot | proxy_score | CCS | CCS_var | Refine% |
|-----------|----|----|-----------|:-----------:|:---:|:-------:|:------:|
| s030_cem030_t0 | 0.30 | -0.30 | 0 | 0.2587 | 1.0000 | 0.0000 | 20 |
| s050_cem020_t0 | 0.50 | -0.20 | 0 | 0.2587 | 1.0000 | 0.0000 | 20 |
| s035_cem005_t0 | 0.35 | -0.05 | 0 | 0.2587 | 1.0000 | 0.0000 | 20 |
| s040_cem030_t0 | 0.40 | -0.30 | 0 | 0.2587 | 1.0000 | 0.0000 | 20 |
| s040_cem025_t0 | 0.40 | -0.25 | 0 | 0.2587 | 1.0000 | 0.0000 | 20 |
| s040_cem020_t0 | 0.40 | -0.20 | 0 | 0.2587 | 1.0000 | 0.0000 | 20 |
| s040_cem015_t0 | 0.40 | -0.15 | 0 | 0.2587 | 1.0000 | 0.0000 | 20 |
| s040_cem010_t0 | 0.40 | -0.10 | 0 | 0.2587 | 1.0000 | 0.0000 | 20 |
| s040_cem005_t0 | 0.40 | -0.05 | 0 | 0.2587 | 1.0000 | 0.0000 | 20 |
| s045_cem030_t0 | 0.45 | -0.30 | 0 | 0.2587 | 1.0000 | 0.0000 | 20 |

Default config proxy_score: 0.2425 (rank 157 of 168)
Best fixed proxy_score:    0.2587 (Δ = +0.0162)

### Adaptive thresholds — all configs (sorted by proxy_score)

| Config ID | sim_pct | ce_pct | proxy_score | CCS | CCS_var | Refine% |
|-----------|:-------:|:------:|:-----------:|:---:|:-------:|:------:|
| adaptive_s60_c40 | 60 | 40 | 0.2425 | 1.0000 | 0.0000 | 0 |
| adaptive_s50_c50 | 50 | 50 | 0.2425 | 1.0000 | 0.0000 | 0 |
| adaptive_s70_c30 | 70 | 30 | 0.2425 | 1.0000 | 0.0000 | 0 |
| adaptive_s60_c30 | 60 | 30 | 0.2425 | 1.0000 | 0.0000 | 0 |

**Fixed vs Adaptive (proxy_score):**  best fixed = 0.2587 (s030_cem030_t0),  best adaptive = 0.2425 (adaptive_s60_c40),  Δ = -0.0162

## PUBMEDQA

### Fixed thresholds — top-10 by proxy_score

| Config ID | sim | ce | topk_prot | proxy_score | CCS | CCS_var | Refine% |
|-----------|----|----|-----------|:-----------:|:---:|:-------:|:------:|
| s050_cem010_t0 | 0.50 | -0.10 | 0 | 0.2820 | 1.0000 | 0.0000 | 40 |
| s055_cem015_t0 | 0.55 | -0.15 | 0 | 0.2820 | 1.0000 | 0.0000 | 40 |
| s050_cem030_t0 | 0.50 | -0.30 | 0 | 0.2820 | 1.0000 | 0.0000 | 40 |
| s055_cem005_t0 | 0.55 | -0.05 | 0 | 0.2820 | 1.0000 | 0.0000 | 40 |
| s050_cem005_t0 | 0.50 | -0.05 | 0 | 0.2820 | 1.0000 | 0.0000 | 40 |
| s060_cem030_t0 | 0.60 | -0.30 | 0 | 0.2820 | 1.0000 | 0.0000 | 40 |
| s055_cem020_t0 | 0.55 | -0.20 | 0 | 0.2820 | 1.0000 | 0.0000 | 40 |
| s060_cem025_t0 | 0.60 | -0.25 | 0 | 0.2820 | 1.0000 | 0.0000 | 40 |
| s050_cem025_t0 | 0.50 | -0.25 | 0 | 0.2820 | 1.0000 | 0.0000 | 40 |
| s060_cem020_t0 | 0.60 | -0.20 | 0 | 0.2820 | 1.0000 | 0.0000 | 40 |

Default config proxy_score: 0.2496 (rank 142 of 168)
Best fixed proxy_score:    0.2820 (Δ = +0.0324)

### Adaptive thresholds — all configs (sorted by proxy_score)

| Config ID | sim_pct | ce_pct | proxy_score | CCS | CCS_var | Refine% |
|-----------|:-------:|:------:|:-----------:|:---:|:-------:|:------:|
| adaptive_s60_c40 | 60 | 40 | 0.2496 | 1.0000 | 0.0000 | 0 |
| adaptive_s50_c50 | 50 | 50 | 0.2496 | 1.0000 | 0.0000 | 0 |
| adaptive_s70_c30 | 70 | 30 | 0.2496 | 1.0000 | 0.0000 | 0 |
| adaptive_s60_c30 | 60 | 30 | 0.2496 | 1.0000 | 0.0000 | 0 |

**Fixed vs Adaptive (proxy_score):**  best fixed = 0.2820 (s050_cem010_t0),  best adaptive = 0.2496 (adaptive_s60_c40),  Δ = -0.0324

