# Area Chair Synthesis

## Status

This addresses the current/initial AC meta-review by `Ji7w`. It is not
described as the final meta-review.

## Paste-ready synthesis

We appreciate the AC’s balanced assessment: evaluation instability,
fixed-output scorer sensitivity, audit artifacts, and cost-aware reporting are
valuable, while the current paper needs materially better accessibility,
scope control, evidence grading, and practitioner guidance.

No revised paper can be uploaded during rebuttal, so we clarify the claim
boundary here and describe camera-ready changes if accepted. Our central
clarification is to separate method from numerical generalization.
ControlledRAG is a practical disclosure and audit procedure: authors report
the generator, retrieval setup, context construction, measurement/scorer,
human calibration, threshold transfer, and cost, then stress-test only
reasonable alternatives that are critical to the claim. The seven categories
are neither mathematically unique nor formally exhaustive. The numerical
findings remain bounded primarily to
short-answer QA and 7B-class local generators; the five-dataset threshold
grid, two-dataset cost comparison, retriever diagnostics, one Qwen2.5-7B
probe, and 40-question long-form panel provide diagnostic breadth, not broad
validation of modern, agentic, or complex RAG.

We grade support rather than imply equal validation: fixed-output
scorer/input-format evidence is strongest; human and matched-context evidence
is medium-strength; generator, retriever, cost, and long-form probes are
bounded or exploratory. No modern-judge result exists. The repaired optional
package remains `PROMPT_05_REPAIRED_PREPARED_NOT_EXECUTED`, with zero model
loads, network calls, or real rows scored.

If accepted, we will rewrite the camera-ready abstract, introduction, setup,
and experiment organization around plain definitions and one evidence map.
The legacy NLI scores are
answer-only zero-shot label proxies; the custom third scorer is RAGAS-style,
not official RAGAS. Figure 2 keeps answers, contexts, and backbones fixed and
changes only scorer input: on 194 complete pairs, the mean contrast changes
from `+0.017` to `-0.279` for DeBERTa and from `+0.044` to `-0.081` for the
second backbone. This establishes input-format sensitivity, not universal
correctness. We will also justify every axis using the stated
reasonable-substitution criterion.

For practitioner guidance, our protocol requires a declared deployment
endpoint and constraints, deployment-relevant human calibration,
claim-critical stress tests, and a stable/conditional/unresolved
classification. Multi-objective choices use a Pareto-first rule with explicit
weights or constraints; when plausible choices disagree, the output is a
conditional set, not a universal winner.

Finally, we add Cattan et al., “DRAGged into Conflicts” (arXiv:2506.08500,
2025) and distinguish contradictory retrieved sources from scorer
disagreement. We did not complete a contradictory-context experiment. If
accepted, the camera-ready will also provide a canonical
experiment/data/code map while accurately labeling recovered versus submitted
rows and avoiding a universal artifact completeness claim.
