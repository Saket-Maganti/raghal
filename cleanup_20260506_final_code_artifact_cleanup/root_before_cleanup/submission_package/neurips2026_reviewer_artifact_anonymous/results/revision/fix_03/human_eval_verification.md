# Human Evaluation Verification

Computed from `data/revision/fix_03/human_eval_rater_a.csv`, `data/revision/fix_03/human_eval_rater_b.csv`, `data/revision/fix_03/human_eval_adjudicated.csv`, and `data/revision/fix_03/human_eval_template.jsonl`.

- n: 99
- raters: 2
- raw agreement: 0.919192 (91 of 99 exact-match)
- Cohen's kappa: 0.773779
- adjudicated labels: 79 supported, 16 partially supported, 4 unsupported

| Metric | Spearman rho | Pearson r | Kendall tau-b |
| --- | ---: | ---: | ---: |
| DeBERTa-v3 NLI | 0.103023 | 0.110258 | 0.083292 |
| Second NLI | 0.393969 | 0.403683 | 0.325170 |
| RAGAS-style judge | 0.548699 | 0.449566 | 0.527443 |

Status: recomputed from the adjudicated file after case-by-case disagreement review.
