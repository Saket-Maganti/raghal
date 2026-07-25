# Prompt B red team

Date: 25 July 2026.

## Scientific validity

1. **Yes.** All 1,510 request keys were received.
2. **Yes.** The three threshold-inconsistent outputs remain invalid.
3. **Yes.** No output was repaired, imputed, or manually recoded.
4. **Yes.** Every row carries the pinned model identity.
5. **Yes.** Every row carries the immutable revision recorded in the run receipt.
6. **Qualified.** The accepted run's locks and diagnosis identify left padding as the only execution change. The missing separately named repair ZIP prevents an independent cross-package confirmation.
7. **Blocked.** Raw-output identity between the repair ZIP and postprocessed ZIP cannot be checked because the separately named repair ZIP was not located. Shard-to-merged identity inside the accepted ZIP does pass.
8. **Yes.** Independent strict parsing gives a 99.801% validity rate, complete keys, no duplicate or unexpected keys, and no identity errors.
9. **Yes.** Differential missingness is 0.781 percentage points, below two points.
10. **Yes.** All primary paired estimates use the 193-row common-complete set.
11. **Yes.** The 83-row typical slice and 72-row disagreement-targeted slice are separate.
12. **Yes.** The 72-row slice is labelled diagnostic throughout.
13. **Yes.** Point estimates are direct observed differences.
14. **Yes.** Constant-resample Spearman values are omitted only from that replicate; 9,991 finite diagnostic replicates remain.
15. **Yes.** The frozen seed is 20260724 for each bootstrap analysis.
16. **Yes.** Each reported bootstrap requests exactly 10,000 paired replicates.
17. **Yes.** Finite counts are 10,000 except typical AP/Spearman (9,822), diagnostic Spearman (9,991), and diagnostic AP (10,000).
18. **Yes.** Primary analyses follow the frozen populations and estimands; robustness checks are labelled post hoc.
19. **Yes.** Wording says same direction with a material change, never sign reversal.
20. **Yes.** Universal evaluator or system superiority is explicitly rejected.

## Rebuttal strategy

21. **Yes.** Each field opens with the reviewer's principal decision-relevant concern.
22. **Yes.** The Area Chair field includes a concern-to-resolution table and Stable/Conditional/Unresolved guidance.
23. **Yes.** uqxN receives the pinned modern-judge result and the seven-category simplification.
24. **Yes.** wXNA receives same-row AP and Spearman comparisons on both audited human slices.
25. **Yes.** diyB receives an experiment map with population, estimand, result, and scope.
26. **Yes.** d61o receives bounded scope plus the contemporary-judge audit.
27. **Yes.** wh9X receives metric definitions, Figure 2 clarification, seven-category guidance, and conflict handling.
28. **Yes.** The Cattan et al. reference is used only for its relevant methodological point.
29. **Yes.** Completed analyses are in past tense; manuscript changes remain future tense.
30. **Yes.** The new audit is compact and does not replace the paper's central reporting-standard contribution.

## Privacy and release

31. **Yes.** No private row-level records are staged.
32. **Yes.** No individual human labels are staged.
33. **Yes.** No raw model outputs are staged.
34. **Yes.** The release scan finds no absolute local path.
35. **Yes.** The release scan finds no credential or token.
36. **Yes.** ZIPs and extracted private workspaces remain untracked and locally excluded.
37. **Yes.** All six preferred and six fallback fields are below 10,000 characters.
38. **Yes.** Generated Markdown and plain-text packages are synchronized.
39. **Yes.** The fallback is complete and independent of the new result.
40. **Yes.** Professor approval is still required; submission was not performed.

## Paper–artifact identity

41. **Yes.** The cleaned artifact is mapped to the authoritative 25-page ControlledRAG paper by exact title, page audit, and PDF SHA-256.
42. **Yes.** Later or unrelated paper identities are excluded from the review-facing artifact.
43. **Yes.** The pre-cleanup source base and preservation refs are recorded.
44. **Blocked.** The mirror's branch/refresh configuration is not exposed by its read endpoint, and its live README has not refreshed to the published source `main`.
45. **Yes.** Visible release titles use the authoritative title.
46. **Yes.** No paper PDF is present on the review-facing branch.
47. **Yes.** Release mechanics and demonstration language are separated from claims supported by the paper.

## Mathematical transparency

48. **Yes.** Aggregate validation has a documented one-command path.
49. **Yes.** Central equations map to the compact metric implementation.
50. **Yes.** Nineteen tests include hand-checkable estimator and direction cases.
51. **Yes.** Positive class, score direction, and contrast direction are explicit.
52. **Yes.** Observed data produce all point estimates.
53. **Yes.** Resampling is paired at the row level for every difference.
54. **Yes.** Finite-replicate counts accompany every reported interval.
55. **Yes.** AP, Spearman, balanced accuracy, F1, and Brier are defined and interpreted separately.
56. **Yes.** The historical 99/100 counts are not conflated with the modern 83/72 slices.
57. **Yes.** The stale-value scan passes; only approved historical calibration values remain.
58. **Yes.** Diagnostic and post-hoc analyses are labelled as such.

## Codebase and anonymity

59. **Yes.** `.DS_Store` is absent.
60. **Yes.** Caches, model downloads, raw vectors, raw outputs, and row-level records are absent.
61. **Yes.** `src/controlledrag/metrics.py` is the canonical public implementation.
62. **Yes locally.** The documented smoke command and release validator pass; a clean GitHub workflow is included.
63. **Yes.** The release validator exits on the first failed invariant.
64. **Yes.** The source-artifact identity scan passes.
65. **Yes.** No notebook is released; cache files and generated metadata are excluded.
66. **Yes.** The OpenReview response fields contain no source GitHub URL.
67. **Blocked.** The anonymous mirror is readable but still shows the pre-cleanup README, so visual/current-state verification is incomplete.
68. **Yes.** Rebuttal and handoff wording say mirror refresh is required and do not imply otherwise.

## Reviewer-confidence response

69. **Yes.** The responses address evidence and scope without commenting on reviewer expertise.
70. **Yes.** wXNA can verify the same-row result from one compact human-calibration table.
71. **Yes.** diyB and wh9X receive a mathematical walkthrough and a short verification path.
72. **Yes.** uqxN and d61o receive new bounded evidence plus concrete revision commitments.
73. **Yes.** The Area Chair receives a concern-to-resolution table.
74. **Yes.** Every response states its scope or a non-claim boundary.

## Human readiness

75. **Yes.** The author pack gives a sub-two-minute explanation of the paired difference in contrasts.
76. **Yes.** It distinguishes left-padding execution repair from output repair.
77. **Yes.** The professor one-page decision sheet is complete.
78. **Yes.** Likely discussion questions and bounded answers are prepared.
79. **Yes.** OpenReview rendering review and submission remain manual.
80. **Yes.** No rebuttal claim has been submitted before mirror verification.

## Status

`BLOCKED_BY_MISSING_REPAIR_ZIP_FOR_CROSS_ZIP_IDENTITY_AND_ANONYMOUS_MIRROR_REFRESH`

The accepted run, strict parsing, populations, aggregate estimates, and release scans pass. The two blockers concern provenance equivalence across a missing archive and the stale anonymous mirror, not the recomputed numerical results.
