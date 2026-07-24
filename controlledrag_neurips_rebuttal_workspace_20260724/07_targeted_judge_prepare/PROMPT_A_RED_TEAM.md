
# Prompt A red-team

1. Row joins defensible? **Yes**—locked source indices/IDs and same source
   payloads; no unsupported filename-only join.
2. Human labels final/adjudicated? **Yes**; intermediate typical labels are
   excluded from the binary bridge.
3. Slices separate? **Yes**.
4. Answer-only omits only context? **Yes**; normalized prompt diff passes.
5. Prompt wording bias? **No detected asymmetry** beyond visible evidence.
6. Immutable model identity? **Yes**, `a09a35458c702b33eeacc393d103063234e8bc28`.
7. Silent model switch? **No**; ID/revision checked in input, both shards, and
   output validation.
8. Silent precision switch? **No**; NF4/float16 is fatal-on-failure.
9. Silent truncation/drop? **No**; right-only context truncation is recorded;
   missingness is explicit.
10. Malformed outputs preserved? **Yes**.
11. Differential missingness measured? **Yes** by system and interface.
12. Metrics frozen? **Yes**, before inference.
13. Favorable post-hoc selection possible? **Not under the contract**; one
    model, one revision, two frozen interfaces.
14. Same row scored once per interface? **Yes** after global semantic dedup.
15. Baseline/HCPC-v1 pairs valid? **Yes**; primary analysis uses the 194
    locked historically complete pair IDs.
16. Duplicate significance inflation? **Prevented**; 28 disagreement records
    are excluded for within/cross-panel duplication.
17. AP positive class? **faithful=1**, sklearn average precision.
18. Current rebuttal untouched? **Yes**, protected hashes rechecked.
19. Private ZIP excluded from Git? **Yes**, outside Git and locally excluded.
20. Worth rebuttal time? **Yes, conditionally**: 600-row main plus one valid
    83-row same-row bridge directly addresses the most important unresolved
    judge/interface concern; the 72-row disagreement diagnostic must remain
    qualified.

Status: `PASS_PREPARED_NOT_EXECUTED`
