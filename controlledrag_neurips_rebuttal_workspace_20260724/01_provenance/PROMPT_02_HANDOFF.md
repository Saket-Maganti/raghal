# Prompt 02 Handoff

## Outcome

Prompt 02 is complete with a passing P0 gate and explicit quarantines.
Fifty-six of 62 ledger claims are verified; four are mismatches, one awaits
immutable provenance, and one is not rebuttal-safe.

## Prompt 3 safe inputs

Prompt 3 may use:

- the upgraded `CLAIM_TO_EVIDENCE_LEDGER.csv`;
- `PROMPT_02_RECOMPUTED_RESULTS.json`;
- the fixed-data sources and hashes in
  `FULL_PER_QUERY_PROVENANCE_REPORT.md`;
- the AUPRC convention in `AUPRC_CONVENTION_LOCK.md`;
- only claim rows whose status is `VERIFIED_EXACT`,
  `VERIFIED_WITH_ROUNDING`, or `VERIFIED_SUMMARY_ONLY`, and only within each
  row's safety language.

## Mandatory exclusions

Prompt 3 must not:

- use stale AUPRC values;
- use matched-test `p=0.011`;
- pool the two human-evaluation slices;
- describe re-encoding as fresh retrieval/generation;
- describe context-conditioned NLI as universally correct;
- claim universal submitted per-query coverage;
- assert immutable preregistration timing, compensation, or IRB status.

## Human-evaluation handoff

- `n=99`: pre-adjudication agreement `0.919192`, kappa `0.773779`;
  adjudicated distribution `79/16/4`; alignment uses adjudicated labels.
- `n=100`: pre-adjudication agreement `0.880000`, kappa `0.720930`;
  12 disagreements; adjudicated distribution `74/26/0`.
- The ID overlap is zero and the label schemas differ.

## AUPRC handoff

Locked submitted `sklearn` AUPRC is
`0.764813 / 0.928793 / 0.859367`. The historical
`0.761753 / 0.928433 / 0.886240` triple is forbidden.

## Remaining blockers

- Exact review/meta-review text remains unavailable from Prompt 1.
- The matched binary `p=0.011` mismatch remains unresolved; safe replacement
  is exact two-sided `p=0.013531`, with convention stated, or no p-value.
- No immutable pre-result Git evidence was located for the claimed
  `2026-04-26` pre-specification date.
- The target GitHub repository is public, so pushing remains blocked.

## Prompt 3 readiness

`READY_WITH_QUARANTINED_EXCLUSIONS`

Prompt 3 can proceed on the verified fixed-data surface without any new model
run or modern-judge result.
