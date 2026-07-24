# P0 Integrity Gate

## Status: PASS WITH QUARANTINED EXCLUSIONS

The gate passes because all unresolved or contradicted items are explicitly
excluded from proposed rebuttal text. The pass is conditional on preserving
the exclusions below.

| Gate check | Result |
| --- | --- |
| Submitted AUPRC convention locked | PASS |
| Stale AUPRC values excluded | PASS |
| `n=99` and `n=100` kept separate | PASS |
| Matched mean effect/test/CI reproduced | PASS |
| Unreproduced `p=0.011` excluded | PASS |
| Output origins distinguished | PASS |
| Re-encoding not called fresh retrieval/generation | PASS |
| Context-conditioned NLI not called universally correct | PASS |
| Universal artifact-completeness claim excluded | PASS |
| Unsupported preregistration/IRB/compensation claims excluded | PASS |
| No model or external API run performed | PASS |

## Allowed numerical inputs

Rebuttal drafting may use only claims marked `VERIFIED_EXACT`,
`VERIFIED_WITH_ROUNDING`, or `VERIFIED_SUMMARY_ONLY` in
`CLAIM_TO_EVIDENCE_LEDGER.csv`, subject to each row's rebuttal-safety
language.

Rows marked `MISMATCH`, `PROVENANCE_MATCH_PENDING`, or
`NOT_REBUTTAL_SAFE` are forbidden unless a later prompt supplies and verifies
new evidence.

## Automatic failure conditions

The P0 gate fails if a draft:

- uses any quarantined value from `DO_NOT_USE_STALE_VALUES.md`;
- pools the human slices;
- omits the fixed-row/rescoring qualifier where required;
- upgrades a pilot or exploratory probe into a generalization claim;
- claims complete submitted per-query coverage;
- asserts immutable preregistration timing without new evidence.
