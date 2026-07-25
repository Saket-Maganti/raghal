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
