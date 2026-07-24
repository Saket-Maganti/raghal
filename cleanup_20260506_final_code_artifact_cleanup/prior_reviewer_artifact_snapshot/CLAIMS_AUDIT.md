# Claims Audit

This audit records where each reported numerical value can be checked in the
anonymized artifact.

## Matched-Context Audit

| Claim | Source |
| --- | --- |
| HIGH-LOW faithfulness = -0.002 | `results/revision/fix_01/paired_wilcoxon.csv` |
| Paired Wilcoxon p = 0.628 | `results/revision/fix_01/paired_wilcoxon.csv` |
| Cohen's d_z = -0.017 | `results/revision/fix_01/paired_wilcoxon.csv` |
| 95% bootstrap CI [-0.022, +0.017] | `results/revision/fix_01/bootstrap_ci.csv` |
| HIGH hallucination 16.5%, LOW hallucination 9.0% | `results/revision/fix_01/paired_wilcoxon.csv` |

## Scaled Audit

| Claim | Source |
| --- | --- |
| Pooled means 0.661 / 0.650 / 0.661 | `results/revision/fix_02/headline_table.csv` |
| Hallucination 14.6% / 14.7% / 14.3% | `results/revision/fix_02/headline_table.csv` |
| Wilson CI lower bound on baseline hallucination 13.3% | `results/revision/fix_02/headline_table.csv` |
| Per-seed Wilcoxon summaries | `results/revision/fix_02/paired_contrasts.csv` |

## Metric Fragility

| Claim | Source |
| --- | --- |
| Mistral DeBERTa raw 0.011 | `results/revision/fix_03/standardized_scorer_fragility.csv` |
| Mistral second NLI raw 0.032 | `results/revision/fix_03/standardized_scorer_fragility.csv` |
| Mistral RAGAS-style raw 0.140 | `results/revision/fix_03/standardized_scorer_fragility.csv` |
| z-scored DeBERTa 0.071 | `results/revision/fix_03/standardized_scorer_fragility.csv` |
| z-scored second NLI 0.231 | `results/revision/fix_03/standardized_scorer_fragility.csv` |
| z-scored RAGAS-style 0.337 | `results/revision/fix_03/standardized_scorer_fragility.csv` |
| Cross-scorer Pearson correlations | `results/revision/fix_03/metric_correlations.csv` |

## Context-Conditioned NLI

| Claim | Source |
| --- | --- |
| Legacy DeBERTa baseline-v1 = +0.017 | `results/revision/context_conditioned_nli/contrasts_n600.csv` |
| Context-conditioned DeBERTa = -0.279 | `results/revision/context_conditioned_nli/contrasts_n600.csv` |
| Legacy second NLI = +0.044 | `results/revision/context_conditioned_nli/contrasts_n600.csv` |
| Context-conditioned second NLI = -0.081 | `results/revision/context_conditioned_nli/contrasts_n600.csv` |
| n=99 alignment Spearman values | `results/revision/context_conditioned_nli/n99_alignment_spearmans.csv` |

## Human Evaluation

| Claim | Source |
| --- | --- |
| n=99, raw agreement 0.919, kappa 0.774 | `human_eval_final/n99_calibration/human_eval_summary.csv` |
| n=99 distribution 79 / 16 / 4 | `human_eval_final/n99_calibration/human_eval_label_distribution.csv` |
| n=99 Spearman 0.103 / 0.394 / 0.549 | `human_eval_final/n99_calibration/human_eval_correlations.csv` |
| n=100, raw agreement 0.88, kappa 0.721 | `human_eval_final/n100_disagreement/human_disagreement_agreement.csv` |
| n=100 distribution 74 / 26 / 0 | `human_eval_final/n100_disagreement/human_disagreement_label_distribution.csv` |
| n=100 Spearman -0.156 / 0.446 / 0.384 | `human_eval_final/n100_disagreement/human_disagreement_correlations.csv` |
| n=100 AUROC 0.398 / 0.794 / 0.718 | `human_eval_final/n100_disagreement/human_disagreement_auroc_auprc.csv` |

## Cost-Aware Head-To-Head

| Claim | Source |
| --- | --- |
| SQuAD faithfulness 0.698 / 0.708 / 0.710 | `results/revision/fix_06/h2h_summary_with_ci.csv` |
| HotpotQA faithfulness 0.643 / 0.633 / 0.631 | `results/revision/fix_06/h2h_summary_with_ci.csv` |
| SQuAD hallucination 12.0% / 12.5% / 12.5% | `results/revision/fix_06/h2h_summary_with_ci.csv` |
| HotpotQA hallucination 10.5% / 12.5% / 13.0% | `results/revision/fix_06/h2h_summary_with_ci.csv` |
| Latency and indexing costs | `results/revision/fix_06/h2h_summary_with_ci.csv` |

## Follow-Up Diagnostics

| Diagnostic | Source |
| --- | --- |
| Threshold transfer | `results/revision/fix_04/` |
| Coherence vs noise | `results/revision/fix_05/` |
| Answer-span/control diagnostic | `source_tables/span_control_summary.csv` |
| Retriever sanity check | `source_tables/retriever_sanity_summary.csv` |
| Second-generator metric fragility | `source_tables/second_generator_metrics.csv` |
| Long-form stress test | `source_tables/longform_stress_summary.csv` |
