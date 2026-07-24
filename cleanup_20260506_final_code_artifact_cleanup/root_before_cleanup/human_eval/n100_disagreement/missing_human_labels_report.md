# Annotation Completeness Report

Input file: `annotation_batch_disagreement_100.csv`
Total rows: 100

## Two-rater + adjudication completeness

| Column | Filled Count | Missing Count | % Complete |
| --- | --- | --- | --- |
| `annotator_label` | 0 | 100 | 0.0% |
| `human_label_rater1` | 100 | 0 | 100.0% |
| `human_label_rater2` | 100 | 0 | 100.0% |
| `adjudicated_label` | 100 | 0 | 100.0% |
| `adjudicated_confidence` | 100 | 0 | 100.0% |

**Status: COMPLETE.** All 100 rows have rater 1, rater 2, and adjudicated labels. Of the 100 items, 12 had rater-rater disagreement; rater-rater disagreements are resolved in `human_eval_adjudicated.csv` (column `adjudication_notes`).
