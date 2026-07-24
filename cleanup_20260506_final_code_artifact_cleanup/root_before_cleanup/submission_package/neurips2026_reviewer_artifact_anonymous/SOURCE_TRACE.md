# Source Trace

This file maps reported numerical values to frozen files in the anonymized
artifact. It contains no paper source, paper PDF, public demo, or internal
history.

## Core Result Files

- Matched-context audit: `results/revision/fix_01/`
- Scaled audit summaries: `results/revision/fix_02/`
- Metric-fragility summaries: `results/revision/fix_03/`
- Context-conditioned NLI summaries: `results/revision/context_conditioned_nli/`
- Threshold transfer: `results/revision/fix_04/`
- Coherence-vs-noise summaries: `results/revision/fix_05/`
- Cost-aware head-to-head summaries: `results/revision/fix_06/`
- RAPTOR-2L cost table: `results/revision/fix_11/`
- Follow-up diagnostics: `results/revision/fix_12/` through `results/revision/fix_15/`
- Compact table inputs: `source_tables/`

## Human-Evaluation Files

The final human-evaluation files are under `human_eval_final/`.

### n=99 Typical-Row Calibration

- `human_eval_final/n99_calibration/human_eval_adjudicated.csv`
- `human_eval_final/n99_calibration/human_eval_n99_with_context.csv`
- `human_eval_final/n99_calibration/human_eval_summary.csv`
- `human_eval_final/n99_calibration/human_eval_label_distribution.csv`
- `human_eval_final/n99_calibration/human_eval_correlations.csv`
- `human_eval_final/n99_calibration/bootstrap_correlation_cis.csv`
- `human_eval_final/n99_calibration/human_eval_verification.csv`

Expected verification values:

- `n=99`
- raw agreement `0.919`
- Cohen's kappa `0.774`
- adjudicated distribution `79/16/4`
- Spearman correlations `0.103/0.394/0.549`

### n=100 Targeted Disagreement Slice

- `human_eval_final/n100_disagreement/annotation_batch_disagreement_100.csv`
- `human_eval_final/n100_disagreement/human_eval_rater1.csv`
- `human_eval_final/n100_disagreement/human_eval_rater2.csv`
- `human_eval_final/n100_disagreement/human_eval_adjudicated.csv`
- `human_eval_final/n100_disagreement/human_disagreement_summary.csv`
- `human_eval_final/n100_disagreement/human_disagreement_label_distribution.csv`
- `human_eval_final/n100_disagreement/human_disagreement_agreement.csv`
- `human_eval_final/n100_disagreement/human_disagreement_correlations.csv`
- `human_eval_final/n100_disagreement/human_disagreement_auroc_auprc.csv`
- `human_eval_final/n100_disagreement/human_disagreement_bootstrap_cis.csv`

Expected verification values:

- `n=100`
- raw agreement `0.88`
- Cohen's kappa `0.721`
- adjudicated distribution `74/26/0`
- Spearman correlations `-0.156/0.446/0.384`
- AUROC `0.398/0.794/0.718`

## Optional Regeneration Inputs

The default reviewer path does not rerun heavy model jobs. Optional scripts in
`experiments/` and selected `scripts/compute_*.py` files use frozen CSVs under
`data/revision/`, `results/revision/`, and `source_tables/` to regenerate or
check derived summaries.

`data/revision/fix_06/per_query_compact.csv` is a compact numeric projection
used by `scripts/compute_cost_headtohead_cis.py`.
