# Discussion-Period Response Bank

Internal use only. Use an answer only if the corresponding issue is raised
during discussion, and preserve every stated claim boundary.

## 1. Why was no modern LLM judge run?

The rebuttal does not need an unvalidated last-minute model result. The
optional package was repaired and tested synthetically, but it remains
`PROMPT_05_REPAIRED_PREPARED_NOT_EXECUTED`: 58 synthetic tests, 0 network
calls, 0 model loads/downloads, and 0 real rows scored. We therefore rely on
the verified fixed-output scorer, human-calibration, and provenance evidence
and state modern-judge validation as missing.

## 2. Why exactly seven categories?

Seven is a practical reporting minimum for this audit, not a mathematical law.
Each category blocks a distinct overclaim: generator, retrieval, and context
specify the answer/evidence process; scorer and human calibration specify
measurement and interpretation; threshold transfer specifies operational
classification; cost specifies deployment choice. Other applications may
need additional categories.

## 3. Is this a position paper?

The paper proposes a reporting protocol, but its empirical contribution is a
controlled self-audit: matched-context, fixed-scorer, fixed-output
scorer-input, human, threshold, and cost audits, plus bounded retriever,
second-generator, and long-form probes. The claim is not a new model, metric,
or comprehensive benchmark; it is an evaluation method supported by bounded
empirical demonstrations.

## 4. How does the framework map to agentic RAG?

Generator maps to the agent/model policy; retrieval to search and tool
selection; context to memory and intermediate observations; measurement to
judge and task-success definitions; calibration to deployment-relevant human
judgments; threshold transfer to intervention or abstention rules; and cost
to latency and tool calls. This is procedural applicability, not evidence
that the current effect sizes transfer to agentic systems.

## 5. Why should recovered rows be trusted?

Recovered rows are not silently relabeled as submitted. The provenance map
hashes their sources, identifies their output origin, and distinguishes
row-reconstructable from summary-verifiable results. Claims whose rows or
conventions cannot support the published wording remain excluded. The
limitation is incomplete universal reviewer-artifact coverage, not permission
to discard provenance boundaries.

## 6. Should one scorer be recommended?

No universal scorer is supported. The tested ordering changes across the
separate human slices, and the fixed-output analysis shows that scorer
interfaces can select different system conclusions. A deployment should
calibrate candidate scorers on a relevant human slice and report the result
as conditional or unresolved when reasonable choices disagree.

## 7. Do seven axes require a factorial experiment?

No. The disclosure tier reports all seven, including “not varied” or “not
measured.” The stress-test tier varies only reasonable alternatives capable
of changing a sign, ranking, threshold decision, or deployment choice.
Experimental burden therefore scales with claim strength.

## 8. How should conflicting outcomes be classified?

If the conclusion survives every tested claim-critical alternative, report it
as stable within the named scope. If it changes under a reasonable scorer,
slice, dataset, threshold, or cost assumption, report the conditions. If
evidence is missing, mismatched, or too weak, leave the claim unresolved.
Disagreement identifies the assumptions that control the conclusion.

## 9. Why would one more dataset not establish broad generalization?

One additional cell can test a specific boundary but cannot identify behavior
across generator, retriever, task, language, judge, and deployment families.
Broad generalization requires a designed coverage argument and calibrated
uncertainty, not a larger-looking dataset count. The current secondary cells
therefore remain diagnostic.

## 10. What concrete camera-ready changes will be made?

The camera-ready will lead with a motivating decision example, state the
claim boundary and metric inputs before results, present one experiment and
provenance map, separate primary controlled audits from bounded probes,
explain Figure 2 in plain language, operationalize the disclosure/stress-test
tiers, and add the conflicting-source citation while stating that no
contradictory-context experiment was completed.

## Novelty boundary

The novelty is not the observation that generators, retrievers, or scorers
matter individually. It is treating their specification as part of the
scientific claim, requiring claim-critical sensitivity analysis, and coupling
the report to human calibration, threshold portability, deployment cost, and
auditable evidence.
