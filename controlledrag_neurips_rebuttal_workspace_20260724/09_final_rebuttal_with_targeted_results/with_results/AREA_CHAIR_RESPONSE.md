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
