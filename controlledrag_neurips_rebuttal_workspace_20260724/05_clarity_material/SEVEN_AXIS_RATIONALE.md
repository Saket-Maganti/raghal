# Seven-Axis Rationale

## Core framing

The seven axes are practical, non-redundant disclosure categories for this
audit. They are not mathematically unique and are not claimed to be formally
exhaustive. Authors should disclose all seven because each blocks a distinct
route from a bounded result to an overbroad claim; they need only stress-test
the reasonable alternatives that are claim-critical.

The inclusion rule is operational: include a category when leaving it
implicit lets a reader substitute another reasonable choice and change the
claim’s interpretation or decision.

| Axis | Required disclosure | Distinct question it answers | Evidence in this audit | Overclaim it blocks |
| --- | --- | --- | --- | --- |
| Generator | Model family/size, decoding, prompt, fixed versus regenerated outputs | Would the result survive a different answer-producing process? | Mistral main cells plus one bounded Qwen2.5-7B probe | Generator-universal language |
| Retriever | Embedder, index, reranker, top-k, refinement policy | Did the retrieval surface, rather than the named system alone, produce the contrast? | MiniLM main cells and bounded BGE/E5/GTE checks | Treating “retrieval quality” as one invariant |
| Context structure | Chunking, order, coherence, similarity, answer-span behavior | What evidence was actually presented to the generator and scorer? | Matched similarity/CCS and re-encoding diagnostics | Treating CCS or similarity as an oracle |
| Scorer | Scorer identity, version, input format, scale, aggregation, threshold | Is the reported conclusion a property of outputs or of measurement choices? | Fixed-output scorer disagreement and Figure 2 sign reversal | Single-metric conclusions without sensitivity |
| Human calibration | Label schema, sampling rule, rater protocol, pre-adjudication agreement, adjudicated alignment | Do automatic scores track human judgments on the relevant slice? | Separate `n=99` typical and `n=100` disagreement-targeted slices | Declaring any automatic scorer universally best |
| Threshold transfer | Selection dataset, selected tau, target matrix, sensitivity | Is a threshold reusable outside the tuning cell? | Mixed 5×5 fixed-output transfer grid | Universal reusable-threshold claims |
| Cost | Latency, indexing, query volume, hardware/external-call assumptions, chosen utility | Is a nominal gain operationally preferable? | Two-dataset point-estimate Pareto and utility sensitivity | Cost-free or universally dominant deployment claims |

## Why these categories are non-redundant

The categories meet different causal or decision roles. Generator and
retriever determine the answer and evidence surface; context structure
describes the evidence object; scorer determines measurement; human
calibration anchors interpretation; threshold transfer governs operational
classification; and cost governs deployment choice. One entry cannot stand
in for another: human agreement does not identify a scorer input, and a
Pareto analysis does not establish threshold transfer.

## Why seven is a minimum here, not a law

This decomposition is a usable reporting minimum for the tested
faithfulness setting. Other studies may need additional categories such as
prompt template, language, safety, privacy, temporal drift, or user
interaction. Those possibilities do not make the present seven arbitrary:
the audit contains direct or diagnostic evidence that each named category can
affect interpretation. They do mean the framework must not be described as a
proof that exactly seven axes exist.

## Disclosure versus stress testing

Every study should fill all seven entries, using “not varied” or “not
measured” where appropriate. Full factorial testing is neither required nor
usually feasible. Stress-test an axis when:

1. the main claim would change if a reasonable alternative changed sign,
   ranking, or deployment choice;
2. prior evidence or a pilot shows material sensitivity;
3. the paper generalizes beyond the tested setting on that axis; or
4. the choice is unusually under-specified or difficult to reproduce.

Otherwise, disclose the fixed choice and narrow the claim. This turns the
checklist into an evidence-budget rule rather than an instruction to run an
unbounded experiment grid.

## Rebuttal-safe concise rationale

> We use seven practical disclosure categories, not a claim of mathematical
> uniqueness or formal exhaustiveness. Each category isolates a distinct
> choice that can change a faithfulness claim or its deployment
> interpretation. We ask authors to disclose all seven and stress-test only
> the reasonable alternatives that are critical to the claim.
