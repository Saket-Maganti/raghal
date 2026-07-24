# Human Disagreement Expansion

This directory contains a targeted annotation batch for scorer-disagreement
calibration. It is not a broad human-evaluation study.

## Source

- Input rows: `data/revision/fix_03/per_query.csv`
- Selected file: `annotation_batch_disagreement_100.csv`
- Previously used IDs excluded when available: 187

## Selection Rule

Rows were ranked by the absolute disagreement between the stored DeBERTa score
and the local RAGAS-style score. The sampler then mixed the strongest
disagreements across:

- DeBERTa high / RAGAS-style low
- RAGAS-style high / DeBERTa low
- near-threshold disagreements around the 0.5 hallucination boundary
- baseline, HCPC-v1, and HCPC-v2 conditions

The goal is to stress-test the central metric-fragility claim where automated
scorers disagree most, not to estimate overall population faithfulness.

## Batch Counts by Condition

- baseline: 34
- hcpc_v1: 33
- hcpc_v2: 33

## Batch Counts by Disagreement Type

- deberta_high_ragas_low: 34
- near_threshold_disagreement: 33
- ragas_high_deberta_low: 33

## Status

**Human annotation is prepared but pending. No human-evaluation results are reported from this batch yet.**

## Files

- `annotation_batch_disagreement_100.csv`: The main batch file containing all examples and scorer metadata.
- `human_eval_instructions.md`: Formal instructions for annotators.
- `human_eval_codebook.md`: Detailed label definitions and decision workflow.
- `human_eval_rater1.csv`: Template for the first independent rater.
- `human_eval_rater2.csv`: Template for the second independent rater.
- `human_eval_adjudication_template.csv`: Template for reconciliation and adjudication.
- `batch_composition.csv`: Statistics on the balance of conditions and disagreement types.
- `scorer_score_summary.csv`: Descriptive statistics of automated scorer outputs for this batch.
- `missing_human_labels_report.md`: Current status of label completion.

## Annotation Protocol

This batch follows a blinded, two-rater plus adjudication protocol:
1. Two independent raters annotate `human_eval_rater1.csv` and `human_eval_rater2.csv`.
2. Annotations are merged into `annotation_batch_disagreement_100.csv` (using `human_label_rater1` and `human_label_rater2` columns).
3. Disagreements are reconciled using the `human_eval_adjudication_template.csv` to produce an `adjudicated_label`.

## Analysis

To run the analysis:

```bash
python3 scripts/analyze_human_disagreement_labels.py \
  --input results/human_disagreement_expansion/annotation_batch_disagreement_100.csv
```

The script robustly handles missing labels by reporting composition and score statistics while marking human-alignment metrics as pending.
