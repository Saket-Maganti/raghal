# Prompt 03 Handoff

## Outcome

Prompt 03 is complete. Both human panels are structurally and numerically
verified without pooling; metric naming and implementation boundaries are
audited; uncertainty, context-calling, threshold, Pareto, cost, and coverage
analyses are complete from fixed outputs only.

## Prompt 4 safe inputs

Prompt 4 may use:

- `02_human_eval/HUMAN_EVAL_VERIFICATION_REPORT.md`;
- `02_human_eval/HUMAN_EVAL_SAFE_NUMBERS.csv`;
- `03_existing_analyses/METRIC_IMPLEMENTATION_AUDIT.md`;
- `03_existing_analyses/EXISTING_ANALYSIS_SUMMARY.md`;
- `03_existing_analyses/NEW_REBUTTAL_SAFE_NUMBERS.csv`;
- `03_existing_analyses/STABILITY_CLASSIFICATION.csv`;
- all Prompt 02 verified claims, subject to the P0 exclusions.

## Strongest safe findings

- Pre-adjudication agreement is 0.919/kappa 0.774 on `n=99` and
  0.880/kappa 0.721 on the separate `n=100` slice.
- Submitted `n=100` sklearn average precision is
  `0.765 / 0.929 / 0.859`; stale values remain forbidden.
- The legacy DeBERTa proxy is weakly aligned on both slices.
- RAGAS-style exceeds second NLI on the typical slice, but their ordering is
  unresolved on the targeted slice; no universal winner may be claimed.
- Context-conditioned fixed re-encoding reverses the sign of the
  baseline-minus-HCPC-v1 contrast relative to both legacy NLI proxies,
  demonstrating metric-calling sensitivity.
- Threshold transfer and SQuAD deployment utility are conditional; CRAG is
  the sole point-estimate three-objective frontier system on HotpotQA.

## Mandatory wording

- Call the historical NLI columns “legacy answer-only zero-shot label
  proxies.”
- Call the custom judge “RAGAS-style,” not official RAGAS.
- Call context results “fixed-context re-encoding,” not fresh retrieval or
  generation.
- State human slice and endpoint with every human metric.
- Use “average precision” or declare the sklearn AP convention.

## Mandatory exclusions

Do not:

- pool `n=99` and `n=100`;
- use the stale AUPRC triple;
- use matched `p=0.011`;
- promote the `n=99` determinate-only AP sensitivity to a headline;
- claim context-conditioned NLI is universally correct;
- claim universal threshold transfer or broad cost dominance;
- claim complete submitted per-query coverage;
- invent review text, preregistration evidence, compensation, IRB details, or
  external-rater identity.

## Remaining blockers

- Exact review/meta-review text and metadata remain unavailable.
- The matched binary p-value mismatch remains unresolved.
- Immutable pre-result evidence for the claimed pre-specification date is
  absent.
- Exact model/package revisions for historical scoring are not locked.
- Artifact-tool spreadsheet inspection remains unavailable because of a
  local native-module signature failure; CSV/Python verification passed.
- The GitHub repository is public, so no push is permitted.

## Prompt 4 readiness

`READY_WITH_QUARANTINED_EXCLUSIONS`

Prompt 4 can build the clarity framework and reviewer guidance from the safe
tables and wording constraints without any modern-judge result.

## Git receipt

- Content commit: `1b230659c51baf4ad893f029eaaae718e0eff3e5`
- Content commit message:
  `rebuttal(p3): validate human evaluation and existing analyses`
- Push status: `PUSH_BLOCKED_REPOSITORY_PUBLIC`
- Push attempted: no
