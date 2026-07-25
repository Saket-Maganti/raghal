Thank you for pressing on contemporary judges, the burden of seven categories, and what an author should do when reasonable metrics disagree.

**Modern judge.** We ran the targeted fixed-output experiment with Qwen2.5-7B-Instruct at a pinned immutable revision. On the same 193 complete baseline-HCPC-v1 pairs:

| Interface | Baseline | HCPC-v1 | Contrast |
| --- | ---: | ---: | ---: |
| answer-only | 8.76 | 5.44 | **3.32** |
| context-conditioned | 37.36 | 23.42 | **13.94** |

The ordering is the same, but exposing context changes the contrast by **10.62 points**, paired 95% CI **[5.54, 15.49]**. The experiment therefore updates our empirical scope beyond the submitted older NLI scorers. It supports material scorer-input sensitivity, not a sign reversal or universal superiority.

All 1,510 requested outputs were received. The frozen strict parser accepted 1,507; three threshold-inconsistent objects were preserved and excluded without repair or imputation. The preregistered strong inclusion gate passes.

**Do all seven categories need exhaustive testing?** No. The categories are practical, non-unique, and non-exhaustive.

| Tier | Requirement |
| --- | --- |
| disclosure | report every relevant category, including "not varied" or "not measured" |
| stress test | vary only reasonable alternatives capable of changing a sign, ranking, threshold decision, or deployment choice |

This is not a seven-dimensional factorial requirement. Experimental effort should scale with claim strength.

**Decision guidance.** Start from the deployment decision. Remove systems dominated on both quality and cost, apply the real latency, indexing, or quality constraints, and audit the evaluator choices that could change the remaining comparison. Report the claim as Stable if its direction survives, Conditional if it depends materially on a defensible choice, or Unresolved if calibration is insufficient.

We will add this two-tier protocol and the Stable/Conditional/Unresolved table to the camera-ready, alongside one compact experiment map and explicit quality-cost trade-offs.
