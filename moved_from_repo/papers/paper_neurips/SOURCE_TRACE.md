# Source Trace

This file maps the review-version claims in `main.tex` and
`supplement.tex` to local result directories. It is intentionally
anonymized: public release, benchmark, repository, and archive links
are omitted from the review version and will be released upon
acceptance.

## Main Claims

| Claim | Paper location | Source |
| --- | --- | --- |
| Matched CCS null: HIGH−LOW faithfulness = −0.002, p = 0.628, CI [−0.022, +0.017] | main §5, supplement §3 | `results/revision/fix_01/` |
| Scaled SQuAD/Mistral audit: 0.661 / 0.650 / 0.661 over 2,500 examples per condition | main §6, supplement §2 | `results/revision/fix_02/` |
| Mistral fixed-generation metric fragility: raw 0.011 / 0.032 / 0.140 and z-scored 0.071 / 0.231 / 0.337 | main §7, supplement §6 | `results/revision/fix_03/`, `results/revision/fix_03/standardized_scorer_fragility.csv`, `scripts/compute_standardized_scorer_fragility.py` |
| Context-conditioned NLI rescoring (n=600 balanced subset): legacy DeBERTa = +0.017 [−0.003, +0.037] → context-conditioned DeBERTa = −0.279 [−0.340, −0.219] (sign-flipped); legacy roberta-large-mnli = +0.044 [+0.026, +0.063] → context-conditioned roberta-large-mnli = −0.081 [−0.122, −0.043] (sign-flipped); n=99 Spearman alignment with adjudicated labels not improved by context-conditioning | main §7 (input-format paragraph), supplement §7 | `scripts/run_context_conditioned_nli_scoring.py`, `results/revision/context_conditioned_nli/per_query_n600.csv`, `results/revision/context_conditioned_nli/contrasts_n600.csv`, `results/revision/context_conditioned_nli/n99_with_ctx_scores.csv`, `results/revision/context_conditioned_nli/n99_alignment_spearmans.csv` |
| **Completed annotation calibration n=99**: κ = 0.774, raw agreement 0.919, label distribution 79 supported / 16 partially_supported / 4 unsupported, Spearman 0.103 / 0.394 / 0.549 against adjudicated label, bootstrap 95% CIs overlap | main §8.1, supplement §12 | `human_eval_final/n99_calibration/human_eval_adjudicated.csv` (combined rater_a + rater_b + adjudicated + notes), `human_eval_final/n99_calibration/human_eval_summary.csv`, `human_eval_final/n99_calibration/human_eval_correlations.csv`, `human_eval_final/n99_calibration/human_eval_label_distribution.csv`, `human_eval_final/n99_calibration/bootstrap_correlation_cis.csv`, `human_eval_final/n99_calibration/human_eval_verification.csv`, `human_eval_final/n99_calibration/human_eval_n99_with_context.csv`, `scripts/verify_human_eval.py` |
| **Completed targeted scorer-disagreement evaluation n=100**: 100/100/100 rater1/rater2/adjudicated complete, raw agreement 0.88, κ = 0.721, adjudicated distribution 74 faithful / 26 hallucinated / 0 unclear, scorer alignment Spearman ρ = −0.156 (DeBERTa) / +0.446 (second NLI) / +0.384 (RAGAS-style), AUROC = 0.398 / 0.794 / 0.718, AUPRC = 0.765 / 0.929 / 0.859 | main §8.2, supplement §13 | `human_eval_final/n100_disagreement/annotation_batch_disagreement_100.csv`, `human_eval_final/n100_disagreement/human_eval_rater1.csv`, `human_eval_final/n100_disagreement/human_eval_rater2.csv`, `human_eval_final/n100_disagreement/human_eval_adjudicated.csv` (rater1, rater2, adjudicated, notes), `human_eval_final/n100_disagreement/human_eval_adjudication_template.csv`, `human_eval_final/n100_disagreement/human_disagreement_summary.csv`, `human_eval_final/n100_disagreement/human_disagreement_label_distribution.csv`, `human_eval_final/n100_disagreement/human_disagreement_agreement.csv`, `human_eval_final/n100_disagreement/human_disagreement_correlations.csv`, `human_eval_final/n100_disagreement/human_disagreement_auroc_auprc.csv`, `human_eval_final/n100_disagreement/human_disagreement_bootstrap_cis.csv`, `scripts/analyze_human_disagreement_labels.py` |
| Threshold-transfer summary and full 5×5 sweep | main §9, supplement §9 | `results/revision/fix_04/` |
| Coherence-preserving vs random retrieval noise slopes (−0.043 vs −0.069) | main §10, supplement §8 | `results/revision/fix_05/` |
| Cost-aware CRAG / HCPC-v2 / RAPTOR-2L head-to-head (no dominator; SQuAD all within 1.2 pp) | main §11 | `results/revision/fix_06/`, `results/revision/fix_06/h2h_summary_with_ci.csv`, `results/revision/fix_11/`, `scripts/compute_cost_headtohead_cis.py` |
| Answer-span/control diagnostic: span and CCS complementary in matched cell | main §5, supplement §3 | `results/revision/fix_12/` |
| Stronger retriever sanity check (matched-pair re-encoding, multi-retriever generation summary) | supplement §4 | `results/revision/fix_13/`, `results/multi_retriever/` |
| Qwen2.5 fixed-generation metric-fragility replication: 0.015 / 0.046 / 0.134 | main §7, supplement §5 | `results/revision/fix_14/` |
| Long-form stress test is exploratory and supplement-only | supplement §6 | `results/revision/fix_15/` |
| Matched HIGH/LOW CCS quantiles and threshold-sensitive hallucination rates | supplement §3 | `results/revision/fix_01/matched_ccs_faithfulness_quantiles.csv`, `results/revision/fix_01/matched_ccs_threshold_rates.csv`, `scripts/compute_matched_ccs_distribution.py` |

## Artifact Manifest (review version)

The reviewer-facing artifact contains:

- per-query CSVs for matched-context, scaled, metric-fragility,
  threshold-transfer, noise, cost-aware-baseline, span-control,
  retriever-sanity, second-generator, and long-form stress runs
- the completed `human_eval_final/n99_calibration/` calibration set
  with both annotation passes, the adjudicated reference labels, the
  bootstrap-CI summary, and the verification trace
- the **completed** `human_eval_final/n100_disagreement/` two-rater
  adjudicated targeted scorer-disagreement evaluation with summary,
  agreement, label-distribution, correlation, AUROC/AUPRC, and
  bootstrap-CI tables
- analysis scripts (`scripts/verify_human_eval.py`,
  `scripts/analyze_human_disagreement_labels.py`,
  `scripts/run_context_conditioned_nli_scoring.py`,
  `scripts/prepare_human_disagreement_eval.py`)
- compiled main paper PDF, supplement PDF, and source LaTeX

Public links and author-identifying release names are withheld for
double-blind review.

## Honest Disclosure on Scorer Implementations

- The DeBERTa-v3 row (`cross-encoder/nli-deberta-v3-base`) and the
  `roberta-large-mnli` row in the main metric-fragility tables are
  **legacy zero-shot label proxies** from the frozen artifact. The
  implementation classifies the answer sentence as the sequence under
  `hypothesis_template="{}"` against the labels
  `entailment / neutral / contradiction`. The retrieved context is
  retained in the per-row data but is **not consumed by these proxy
  calls**. Disclosed in main paper §Setup and §Metric Fragility and
  supplement §Scorer Implementation.
- A separate context-conditioned NLI rescoring (supplement §7) on a
  600-row balanced subset uses the same backbone weights but passes
  the retrieved context as premise. The reported sign of the
  baseline−HCPC-v1 contrast flips for both NLI backbones under that
  calling convention.
- The RAGAS-style row is **context-conditioned by construction**: a
  local Mistral-7B receives the question, retrieved context, and
  answer and returns a support score on [0,1] with a short rationale.
- The metric-fragility tables therefore mix one context-conditioned
  judge with two legacy zero-shot proxies on purpose, because the
  scorer-input-format gap is itself the audit point.

## Honest Disclosure on Human-Eval Slices

- The `n=99` calibration is a **typical-row** stratified sample of the
  7,500 fixed Mistral generations. Bootstrap 95% CIs on the three
  scorer Spearman correlations overlap; we treat the per-scorer
  ordering on this slice as suggestive, not settled.
- The `n=100` evaluation is **targeted/adversarial by construction**:
  rows are sampled to maximise scorer disagreement (legacy DeBERTa
  proxy vs. RAGAS-style judge), balanced across baseline / HCPC-v1 /
  HCPC-v2. It is **not** a population-level faithfulness estimate. The
  scorer ordering on this slice differs from the typical-row ordering;
  that slice-dependence is the load-bearing finding.
- All 12 rater1-vs-rater2 disagreements in the n=100 batch carry
  meaningful adjudication notes; the `human_eval_adjudicated.csv` row
  for each disagreement contains both rater labels and the adjudicator
  rationale.
- The PREANNOTATION CSV (`human_eval_final/n100_disagreement/annotation_batch_disagreement_PREANNOTATION.csv`)
  is a draft/intermediate file from the staging phase and is **not**
  used for any paper claim. It is included only to document the
  pre-rater state of the batch.
