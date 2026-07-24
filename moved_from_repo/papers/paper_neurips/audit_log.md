# Audit Log: Pre-Specified vs. Follow-Up Experiments

This file accompanies `paper_neurips/main.pdf` and
`paper_neurips/supplement.pdf`. It distinguishes experiments that were
**pre-specified** (frozen design committed to the repository before
any results were inspected) from experiments that were added later as
follow-ups. The intent is honest disclosure, not post-hoc
credentialing: a "FOLLOW-UP" label does not weaken the result, but it
does mean the design was chosen with knowledge of the earlier
numbers.

**Scope of "pre-specified".** Each pre-specified fix has a per-fix
log under `experiments/fix_NN_log.md` stating the hypothesis, the
decision rule, the script, and the result. The pre-specification is
**internal**: it relies on this repository's git commit history (the
revision experiment suite was committed before any results were
inspected, with timestamps recorded in this audit_log file). There
is no external OSF or signed-timestamp pre-registration. We therefore
use "pre-specified" rather than "pre-registered" so that no claim of
external pre-registration is made. The exact commit reference is
omitted here for double-blind review and will be added on
acceptance.

## Mapping: Main-Paper Sections to Fixes

| Main paper section                         | Fix     | Status        | Pre-spec date     | Source script |
|--------------------------------------------|---------|---------------|-------------------|---------------|
| §5 Matched-context audit                   | Fix 1   | PRE-SPECIFIED| 2026-04-26        | `experiments/fix_01_*matched_pairs.py` |
| §5 Answer-span/control diagnostic          | Fix 12  | FOLLOW-UP     | added 2026-04-29  | `experiments/fix_12_answer_span_diagnostic.py` |
| §6 Scaled audit (n=2,500 × 5 seeds)        | Fix 2   | PRE-SPECIFIED| 2026-04-26        | `experiments/fix_02_scaled_headline.py` |
| §7 Metric fragility (Mistral, n=7,500)     | Fix 3   | PRE-SPECIFIED| 2026-04-26        | `experiments/fix_03_multimetric_fragility.py` |
| §7 Metric fragility (Qwen2.5, n=100)       | Fix 14  | FOLLOW-UP     | added 2026-04-29  | `experiments/fix_14_second_generator_metric_fragility.py` |
| §8 Human calibration (n=99, two raters)    | Fix 3 (optional annotation arm) | PRE-SPECIFIED  | proto pre-spec 2026-04-26 (stratified n=100, two annotators, Cohen's κ); collection completed 2026-04-28 at n=99 | `results/human_*/` |
| §9 Threshold transfer                      | Fix 4   | PRE-SPECIFIED| 2026-04-26        | `experiments/fix_04_threshold_transfer.py` |
| §10 Coherence vs. noise                    | Fix 5   | PRE-SPECIFIED| 2026-04-26        | `experiments/fix_05_noise_slope.py` |
| §11 Cost-aware baselines (CRAG, HCPC-v2, RAPTOR-2L) | Fix 6 + Fix 11 | PRE-SPECIFIED | 2026-04-26 | `experiments/fix_06_baseline_head_to_head.py`, `experiments/fix_11_raptor_full_table.py` |

## Mapping: Supplement Sections to Fixes

| Supplement section                          | Fix     | Status        | Notes |
|---------------------------------------------|---------|---------------|-------|
| §1 Pre-Specification                        | --      | --            | meta-section, this file is its companion |
| §2 Per-seed scaled detail                   | Fix 2   | PRE-SPECIFIED| same script as §6 main paper |
| §3 Answer-span/control bootstrap CIs        | Fix 12  | FOLLOW-UP     | same script as §5 main paper |
| §4 Stronger retriever sanity                | Fix 13  | FOLLOW-UP     | added 2026-04-29 |
| §5 Second-generator detail                  | Fix 14  | FOLLOW-UP     | same as §7 main paper |
| §6 Long-form stress test                    | Fix 15  | FOLLOW-UP     | added 2026-04-29; exploratory |
| §7 Self-RAG harness-mismatched baseline     | Fix 6 (Self-RAG arm) | FOLLOW-UP-ish | the no-Self-RAG path was pre-specified; the Self-RAG harness-mismatch disclosure was written after attempting the run |
| §8 Coherence vs. noise full slopes          | Fix 5   | PRE-SPECIFIED| same as §10 main paper |
| §9 Threshold transfer full sweep            | Fix 4   | PRE-SPECIFIED| same as §9 main paper |
| §10 Human calibration protocol              | Fix 3 (annotation arm) | see above |
| §11 Source trace and artifact manifest      | --      | --            | bookkeeping |
| §12 Resume and compute notes                | --      | --            | bookkeeping |

## What Pre-Specification Fixed (Before Any Results Were Inspected)

The revision audit pre-specified, on 2026-04-26, the
following decisions for Fixes 1-6, 11:

- The matched-pair construction (similarity gap ≤ 0.02, CCS gap ≥ 0.20).
- The paired Wilcoxon test direction (HIGH > LOW for Fix 1).
- The 10,000-resample bootstrap CI on the mean paired difference.
- The Wilson 95% CI on hallucination rates.
- The seed list {41, 42, 43, 44, 45} for Fix 2.
- The per-seed paired Wilcoxon as the primary significance test for
  Fix 2.
- The three faithfulness scorers (DeBERTa, roberta-large-mnli,
  RAGAS-style) for Fix 3.
- The fixed-context rescore protocol for Fix 3.
- The τ-sweep {0.3, 0.4, 0.5, 0.6, 0.7} and the 5-dataset matrix for
  Fix 4.
- The two-noise-type design (random vs. coherence-preserving) for
  Fix 5.
- The CRAG / HCPC-v2 / RAPTOR-2L head-to-head with n=200 per dataset
  for Fix 6 and Fix 11.
- The optional human-annotation arm of Fix 3: stratified n=100, two
  annotators, Cohen's κ as the inter-rater reliability statistic, and
  Spearman correlation against each automated scorer. Executed at
  n=99 on 2026-04-28; this is therefore counted as pre-specified, not
  follow-up.

The decision rule for Fix 1 was stated explicitly:
"H1 is supported only when the one-sided paired Wilcoxon p-value is
< 0.05, Cohen's dz is > 0.2, the 10,000-resample bootstrap CI on the
mean paired difference excludes 0, and the max similarity gap remains
≤ 0.02 by construction." Fix 1's null result (p = 0.628) was therefore
a pre-committed null, not a post-hoc reframing.

## What Was Added as Follow-Ups (After Initial Results Were Seen)

- Fix 12 (answer-span/control diagnostic) was added after the matched
  intervention came back null. It is a post-hoc constructive
  diagnostic, not a pre-specified confirmation of any new claim. The
  claims made from Fix 12 in main paper §5 are correlational and
  describe in-cell predictors, not new explanatory claims.
- Fix 13 (stronger-retriever sanity check) was added after the
  professor's review asked whether the result depends on the retriever.
  It re-encodes existing matched contexts and incorporates a
  pre-existing multi-retriever generation artifact.
- Fix 14 (Qwen2.5 second-generator replication) was added after the
  professor's review asked whether the metric-fragility result is
  Mistral-specific. It uses n=100 fixed contexts per condition; this
  sample size was chosen post-hoc to fit the local Ollama time budget.
- Fix 15 (long-form stress test) was added as an exploratory
  supplement-only probe; it is described as exploratory in both the
  main paper and the supplement and is not used as broad
  generalization evidence.
- The Self-RAG harness-mismatch disclosure (supplement §7) was written
  after attempting the Self-RAG run; it discloses why we do not
  include a Self-RAG row in the cost-aware head-to-head.

## How to Read the Two Categories Together

A pre-specified null result is the strongest possible evidence we
have that the original claim was over-stated. A follow-up
constructive diagnostic is the weakest evidence in the paper; it
informs but does not confirm. The paper aims to keep this asymmetry
visible: §5 reports the pre-specified Fix 1 null first and the Fix 12
diagnostic after; §7 reports the pre-specified Fix 3 result first and
the Fix 14 replication after.
