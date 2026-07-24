# Rebuttal-Ready Clarity Blocks

These are concise evidence-grounded components, not reviewer-specific final
responses. Exact reviews remain unavailable, so no block is attributed to a
reviewer.

## Metrics

The two historical NLI columns are legacy answer-only zero-shot label proxies:
their default calls do not consume retrieved context. The custom third scorer
is a RAGAS-style judge that receives question, context, and answer; it is not
the official `ragas` package. For the separate disagreement-targeted `n=100`
slice, we use `sklearn.metrics.average_precision_score` with `faithful=1`,
higher scores indicating faithfulness, yielding `0.765/0.929/0.859`.

## Scope

ControlledRAG’s contribution is a bounded audit and disclosure procedure, not
a claim that the reported numerical effects hold for all RAG systems. The
experiments are concentrated in short-answer QA and 7B-class generators, with
bounded retriever, second-generator, threshold, cost, and exploratory
long-form probes; we scope all effect sizes and rankings accordingly.

## Sign flip

Figure 2 holds the 600 answers and contexts fixed and changes only the scorer
call. For the complete baseline/HCPC-v1 pairs, answer-only versus
context-as-premise NLI changes the mean contrast from `+0.017` to `-0.279`
for DeBERTa and from `+0.044` to `-0.081` for the second NLI backbone. This
shows calling-convention sensitivity, not that context-conditioned NLI is
universally correct.

## Experiments

The evidence matrix now identifies each result by dataset/split, `n`,
generator, retriever/context, scorer input, seed status, output origin,
uncertainty method, evidence grade, and source. In particular, fixed-context
re-encoding is labeled separately from fresh generation/retrieval, and
recovered fixed rows are not silently described as submitted artifacts.

## Seven axes

The seven axes are practical, non-redundant disclosure categories, not a
mathematically unique or formally exhaustive taxonomy. Each blocks a distinct
overclaim in this audit. We ask authors to disclose all seven, while
stress-testing only those reasonable alternatives that are critical to the
claim.

## Human evaluation

Two raters—one author and one person external to the project—labeled
independently before reconciliation. Agreement uses pre-adjudication labels;
scorer alignment uses adjudicated labels. The `n=99` typical slice
(agreement `0.919`, kappa `0.774`) and separate `n=100`
disagreement-targeted slice (`0.880`, `0.721`) use different sampling and
label schemas and are never pooled.

## Cost

Cost conclusions are conditional. CRAG is the sole point-estimate
faithfulness/latency/indexing frontier system on HotpotQA, while all three
tested systems remain on the SQuAD frontier. On SQuAD, the illustrative
utility winner changes with query volume and time penalty, so the protocol
reports a Pareto set and deployment assumptions rather than a universal
winner.

## Threshold transfer

Threshold transfer is mixed on the fixed five-dataset grid: rules selected on
PubMedQA, Natural Questions, and TriviaQA are positive on four of five
targets, while SQuAD- and HotpotQA-selected rules are positive on three of
five. HotpotQA recovery is negative at every tested tau. We therefore report
the tuning dataset and transfer matrix rather than claiming a reusable
universal threshold.

## Figure 2

Figure 2 is a measurement-sensitivity plot: same fixed generations, same NLI
backbones, different input conventions, opposite contrast directions. It is
not a new end-to-end experiment and does not identify a universally correct
scorer.

## Practitioner guidance

Practitioners should define the decision and endpoint, disclose all seven
axes, calibrate scorers on a deployment-relevant human slice, stress-test
choices that can change sign or rank, and classify conclusions as stable,
conditional, or unresolved. For multi-objective choices, remove dominated
systems first and apply explicit cost weights only to the remaining Pareto
set.
