# Final OpenReview paste package

Paste each marked field separately. Do not paste the markers.

## Area Chair

<!-- PASTE_START:area_chair -->
Thank you for isolating the issues that matter most for the decision: empirical scope, clarity, practical guidance, and artifact quality. We agree that the paper should be judged as a bounded evaluation audit, not as comprehensive validation of modern RAG.

**What the new evidence changes.** We ran the preregistered targeted experiment requested by the reviews. It uses a pinned Qwen2.5-7B-Instruct judge at an immutable revision, fixed outputs, two scorer interfaces, and no prompt or metric changes.

| Fixed-output result | Answer-only | With context |
| --- | ---: | ---: |
| baseline mean | 8.76 | 37.36 |
| HCPC-v1 mean | 5.44 | 23.42 |
| baseline minus HCPC-v1 | **3.32** | **13.94** |

The system ordering is unchanged, but the contrast increases by **10.62 points**, with paired 95% CI **[5.54, 15.49]**, on the same 193 complete pairs. This is contemporary evidence of scorer-input sensitivity. It is not a modern-judge sign reversal.

We also tested the reviewer's correctness concern through same-row human calibration:

| Human slice | AP: answer / context | Spearman: answer / context |
| --- | ---: | ---: |
| typical determinate, n=83 | **0.963 / 0.982** | **0.118 / 0.251** |
| disagreement-targeted diagnostic, n=72 | **0.799 / 0.864** | **0.053 / 0.299** |

Both slices favor context conditioning, but the second is diagnostic and neither establishes universal correctness. The run received all 1,510 requested outputs; 1,507 passed the frozen strict parser. Three threshold-inconsistent outputs remain invalid and were not repaired or imputed. The preregistered strong inclusion gate passes.

**How we will make the framework actionable.** ControlledRAG is a minimum disclosure and audit protocol. The seven categories are practical, non-unique, and non-exhaustive. Authors disclose every relevant category, then stress-test only alternatives that could change a claim or deployment decision.

| Classification | Meaning | Required action |
| --- | --- | --- |
| Stable | direction survives audited alternatives | report the robustness envelope |
| Conditional | a plausible choice changes the result materially | state that choice and the decision rationale |
| Unresolved | evidence is insufficient or interfaces disagree without calibration | avoid one unconditional claim and collect adjudicating evidence |

The operational sequence is: state the decision; disclose relevant evaluator categories; stress-test claim-critical alternatives; calibrate against humans where possible; classify each claim; report quality-cost trade-offs.

**Scope and presentation revisions.** The submitted evidence remains strongest for controlled short-answer RAG. Threshold, cost, retriever, and second-generator analyses are supporting or diagnostic; the 40-question long-form panel is exploratory. We will lead the camera-ready with one experiment map, define every metric before the results, simplify Figure 2 to show that outputs stay fixed while scorer inputs change, and separate confirmatory evidence from diagnostic probes.

We will also add the missing relation to Cattan et al., "DRAGged into Conflicts: Detecting and Addressing Conflicting Sources in Search-Augmented LLMs," arXiv:2506.08500, 2025. Their work addresses conflicts among retrieved sources; ControlledRAG addresses evaluation choices and claim stability. No contradictory-context experiment is claimed.

Finally, we rebuilt the reviewer artifact around aggregate evidence, claim-to-file traceability, 19 mathematical contract tests, and one fail-closed release validator. Private rows and raw outputs are not public.

The bounded takeaway is now sharper: reasonable evaluator choices can preserve ordering while materially changing effect size, and authors need a practical way to report whether a claim is Stable, Conditional, or Unresolved.
<!-- PASTE_END:area_chair -->

## Reviewer uqxN

<!-- PASTE_START:uqxN -->
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
<!-- PASTE_END:uqxN -->

## Reviewer wXNA

<!-- PASTE_START:wXNA -->
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
<!-- PASTE_END:wXNA -->

## Reviewer diyB

<!-- PASTE_START:diyB -->
Thank you for saying plainly that the current organization makes the work look like a position paper and the codebase hard to assess. The empirical contribution is a controlled self-audit of RAG-faithfulness evaluation, but the paper and artifact did not expose that structure well enough.

**What was actually run.**

| Audit question | Panel | Population | Evidence grade |
| --- | --- | ---: | --- |
| does the scaled retrieval effect persist? | SQuAD/Mistral | 2,500 rows per condition | confirmatory controlled audit |
| does context structure matter at matched similarity? | matched SQuAD | 200 pairs | confirmatory controlled audit |
| can scorer choice change fixed-output conclusions? | fixed Mistral generations | 7,500 rows | confirmatory controlled audit |
| can scorer input change fixed-output conclusions? | balanced panel | 600 rows; 194 primary pairs | confirmatory controlled audit |
| do thresholds transfer? | five datasets x five thresholds | 25 cells | supporting |
| do quality-only rankings survive cost? | SQuAD and HotpotQA | 3 systems x 200 rows per dataset | supporting |
| does a contemporary judge show input sensitivity? | pinned Qwen2.5-7B | 1,510 requests; 193 complete pairs | supporting rebuttal experiment |
| do the two interfaces align differently with humans? | typical and targeted slices | 83 and 72 rows, separate | supporting / diagnostic |
| does the result generalize to long form? | QASPER/MS-MARCO | 40 questions | exploratory |

The new judge result is concrete: the baseline-HCPC-v1 contrast is **3.32** under answer-only scoring and **13.94** with context. The paired difference is **10.62 points**, 95% CI **[5.54, 15.49]**. Same ordering, materially different magnitude.

**Why this is more than a position paper.** The framework is demonstrated through fixed-output interventions, paired estimands, human calibration, threshold transfer, and cost analysis. Its output is an auditable decision protocol, not a new retriever or benchmark.

We also rebuilt the source artifact. The reviewer path now begins with one evidence table and one CPU-safe validation command. Every headline claim maps to an aggregate table, canonical estimator, regression test, and receipt. The release validator checks imports, 19 mathematical contracts, aggregate populations, checksums, privacy, identity, local paths, stale values, README commands, and claim links.

Private questions, contexts, answers, row identifiers, human annotation rows, and raw judge outputs are withheld. The public branch contains aggregate evidence only. Historical code remains recoverable through backup refs rather than cluttering the reviewer path.

We will add the experiment map above to the camera-ready and label each cell confirmatory, supporting, diagnostic, exploratory, or not tested.
<!-- PASTE_END:diyB -->

## Reviewer d61o

<!-- PASTE_START:d61o -->
Thank you for separating the paper's important evaluation question from its narrow short-answer evidence. We agree that the numerical results should not be projected onto arbitrary long-form or agentic RAG.

**Contemporary empirical extension.** We ran a pinned Qwen2.5-7B-Instruct judge on 1,510 fixed-output requests. On the same 193 complete baseline-HCPC-v1 pairs, the answer-only contrast is **3.32 points** and the context-conditioned contrast is **13.94 points**. Their paired difference is **10.62 points**, 95% CI **[5.54, 15.49]**.

This current open-weight judge preserves the system ordering but changes the measured effect magnitude materially. It extends the submitted fixed-output NLI result without regenerating answers or changing the panel.

Same-row human calibration gives bounded evidence about evaluator correctness. On 83 typical determinate rows, context conditioning raises AP from **0.963 to 0.982** and Spearman from **0.118 to 0.251**. A separate 72-row disagreement-targeted diagnostic slice shows the same direction. These are small audited slices, not broad human validation.

**Scope.** The strongest evidence remains controlled short-answer QA with local 7B-class models. The 40-question long-form panel is exploratory. We make no numerical claim about agentic systems, proprietary frontier models, or contradictory retrieved evidence.

ControlledRAG's broader proposal is procedural. In a more complex system, authors should state the task-level decision, disclose the relevant generator/retrieval/context/scorer/calibration/threshold/cost choices, stress-test claim-critical alternatives, and classify the result as Stable, Conditional, or Unresolved. If plausible configurations select different systems and calibration cannot adjudicate them, the claim remains Unresolved.

We will make this boundary explicit in the abstract, evidence map, and limitations, and place confirmatory evidence above supporting and exploratory probes.
<!-- PASTE_END:d61o -->

## Reviewer wh9X

<!-- PASTE_START:wh9X -->
Thank you for identifying the presentation problems so specifically. We agree that the metrics, Figure 2, seven categories, and treatment of conflicting evidence need a simpler path.

**Metrics and Figure 2.**

| Quantity | Plain meaning |
| --- | --- |
| faithfulness score | automated 0-100 support score |
| faithful decision | explicit Boolean, with frozen threshold consistency at score 50 |
| system contrast | paired baseline minus HCPC-v1 score |
| difference in contrasts | context-conditioned contrast minus answer-only contrast |
| AP / Spearman | ranking and rank-alignment against human labels |

The answers do not change in the scorer-input comparison. Only the information given to the evaluator changes.

With a pinned Qwen2.5-7B judge on 193 complete pairs, the system contrast is **3.32 points** answer-only and **13.94 points** with context. The change is **10.62 points**, 95% CI **[5.54, 15.49]**. Both contrasts remain positive. Figure 2 should therefore say "same ordering, materially different magnitude," not imply a modern-judge sign reversal.

**Seven categories.** Generator, retriever, context structure, scorer, human calibration, threshold transfer, and cost are a practical disclosure checklist. They are non-unique and non-exhaustive. Authors disclose all relevant categories but stress-test only alternatives that could change the claim. A full seven-dimensional factorial experiment is not required.

**Conflicting evidence.** When plausible metrics disagree, authors should mark the claim Stable, Conditional, or Unresolved. Conditional claims name the evaluator choice and decision rationale. Unresolved claims remain qualified until human calibration or another adjudicating test is available.

Cattan et al., "DRAGged into Conflicts: Detecting and Addressing Conflicting Sources in Search-Augmented LLMs," arXiv:2506.08500, 2025, study conflicts among retrieved sources. ControlledRAG studies evaluation choices and claim stability. These concerns meet at the retrieval/context category, but no contradictory-context experiment was run here.

We will revise the camera-ready in this order: motivating decision; metric definitions; one experiment map; simplified Figure 2; seven-category disclosure table; Stable/Conditional/Unresolved procedure; evidence grades; scope limitations.
<!-- PASTE_END:wh9X -->
