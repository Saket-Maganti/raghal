# Professor one-page decision sheet

## Recommendation

Preferred package: `09_final_rebuttal_with_targeted_results/with_results/`.

Fallback: `09_final_rebuttal_with_targeted_results/fallback_no_new_results/`.

The preferred package directly answers the modern-judge and same-row calibration concerns. The accepted run is independently recomputed from frozen inputs and accepted raw records. One provenance comparison remains unavailable because the separately named repair ZIP was not located.

## Key result

| Quantity | Result |
| --- | --- |
| answer-only baseline minus HCPC-v1 | 3.32, CI [0.47, 6.27] |
| context-conditioned baseline minus HCPC-v1 | 13.94, CI [9.53, 18.24] |
| difference in contrasts | 10.62, CI [5.54, 15.49] |
| typical human AP / Spearman | 0.963 to 0.982 / 0.118 to 0.251 |
| diagnostic human AP / Spearman | 0.799 to 0.864 / 0.053 to 0.299 |

Interpretation: same ordering, material magnitude change; better context-conditioned alignment on two audited slices. No universal-superiority or sign-reversal claim.

## Integrity

- 1,510 requested and received;
- 1,507 strictly valid;
- three invalid outputs preserved;
- no repair, imputation, pooling, or new inference in Prompt B;
- strong inclusion gate passes;
- all character limits pass;
- source artifact release gates and 19 mathematical tests pass.

## Decision

Use preferred if the accepted-run receipts and independent raw-run validation are sufficient. Use fallback if independent byte identity to the missing separately named repair ZIP is a hard requirement.

Submission remains manual after professor approval and OpenReview preview.
