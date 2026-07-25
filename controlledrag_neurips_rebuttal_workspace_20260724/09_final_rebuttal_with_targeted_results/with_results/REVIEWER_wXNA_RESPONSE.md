Your distinction between measurement sensitivity and measurement correctness is exactly right. We should not assume that giving a scorer context makes it correct.

**We tested that assumption on the same rows.** The new pinned Qwen2.5-7B judge was evaluated against separate human-labelled slices under both interfaces:

| Slice | Metric | Answer-only | With context | Difference |
| --- | --- | ---: | ---: | ---: |
| typical determinate, n=83 | AP | 0.963 | 0.982 | **+0.0189** |
|  | Spearman | 0.118 | 0.251 | **+0.1330** |
| disagreement-targeted diagnostic, n=72 | AP | 0.799 | 0.864 | **+0.0657** |
|  | Spearman | 0.053 | 0.299 | **+0.2463** |

The paired 95% intervals exclude zero for all four direct observed differences. The typical slice is the primary calibration evidence; the disagreement-targeted slice remains diagnostic. We did not pool them.

**Fixed-output system comparison.** On 193 complete pairs, baseline minus HCPC-v1 is **3.32 points** under answer-only scoring and **13.94 points** with context. Their difference is **10.62 points**, paired 95% CI **[5.54, 15.49]**. Both contrasts are positive. The modern judge therefore preserves ordering while changing effect magnitude materially.

The run received all 1,510 outputs. Three score-50 objects contradicted the frozen Boolean threshold and remain invalid. Nothing was repaired or imputed; the strong inclusion gate still passes.

Our corrected interpretation is bounded: context-conditioned scoring aligns better with humans on these two audited slices, and scorer inputs materially condition the system contrast under this pinned judge. This does not prove universal evaluator correctness, universal superiority, or a guaranteed sign reversal.

We will revise the camera-ready to separate continuous score, Boolean decision, and human-alignment estimands; grade the 83-row and 72-row evidence differently; and state the non-claims immediately beside the result.
