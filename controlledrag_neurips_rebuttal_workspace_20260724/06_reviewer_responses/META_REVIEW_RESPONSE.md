# Response to the Current/Initial AC Meta-Review

## Paste-ready response

We appreciate the current AC assessment and agree that the paper’s main risk
is not the importance of the question, but whether a proposed standard is
accessible, empirically scoped, and operationally useful.

No revised paper can be uploaded during rebuttal, so we clarify the claim
boundary here and describe camera-ready changes if accepted. We separate two
claims. **Method:** ControlledRAG is a practical disclosure/audit procedure
with seven categories: generator; retrieval; context construction;
measurement/scorer; human calibration; threshold transfer; and cost. These
are a usable minimum for this audit, not a unique or exhaustive taxonomy;
authors disclose all seven but stress-test only claim-critical alternatives.
**Evidence:** the
numerical findings are bounded mainly to short-answer QA and 7B-class local
generators. The five-dataset threshold grid, two-dataset cost comparison,
retriever diagnostics, one Qwen2.5-7B probe, and exploratory 40-question
long-form panel are diagnostic, not broad validation of complex, agentic, or
modern-judge RAG.

We explicitly grade evidence strength. The fixed-output scorer and input
format analyses are strongest; human and matched-context evidence is
medium-strength; generator, retriever, cost, and long-form cells are bounded
or exploratory. No modern-judge result is claimed: the optional package
remains repaired, prepared, and unexecuted, with zero real rows scored.

If accepted, the camera-ready abstract, introduction, setup, and experiment
organization will be substantially rewritten. Each metric will state its
input, output, direction, aggregation, threshold, and slice. The historical
NLI scores are legacy
answer-only zero-shot label proxies; the custom third scorer is RAGAS-style,
not official RAGAS. Figure 2 holds outputs and backbones fixed and changes only
the scorer input. On 194 complete pairs, the mean contrast changes from
`+0.017` to `-0.279` for DeBERTa and from `+0.044` to `-0.081` for the second
backbone. This demonstrates input-format sensitivity, not that
context-conditioned NLI is universally correct.

Our practitioner protocol is to define the deployment endpoint and
constraints; disclose all seven categories; calibrate on a relevant human
slice; stress-test choices that can change sign, rank, threshold, or deployment
choice; then classify the result as stable, conditional, or unresolved. For
cost-sensitive decisions, apply explicit constraints or weights only after a
Pareto screen. No universal scorer or aggregation rule is claimed.

To address experiment and code clarity, our map lists every cell’s
dataset/split, `n`, generator, retriever/context, scorer input, seed status,
output origin, uncertainty, evidence grade, and canonical source. Recovered
fixed rows will not be described as submitted, and we will not claim complete
per-query coverage.

We also cite Cattan et al., “DRAGged into Conflicts: Detecting and
Addressing Conflicting Sources in Search-Augmented LLMs,” arXiv:2506.08500
(2025). Contradictory retrieved evidence is distinct from scorer disagreement,
and we do not claim a completed contradictory-context experiment.
