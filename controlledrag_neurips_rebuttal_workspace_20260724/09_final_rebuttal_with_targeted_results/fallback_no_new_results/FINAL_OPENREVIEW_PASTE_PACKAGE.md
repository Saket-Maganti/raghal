# Final OpenReview paste package

Paste each marked field separately. Do not paste the markers.

## Area Chair

<!-- PASTE_START:area_chair -->
We thank the AC for identifying clarity, empirical scope, and practitioner
guidance as the central issues. We agree that the numerical findings should be
presented as a bounded audit rather than an evaluation spanning modern RAG. The
contribution we ask the committee to evaluate is precise: ControlledRAG
demonstrates that reasonable evaluation choices can reverse or condition
conclusions and provides an auditable procedure for exposing that dependence.

The contribution is the combination of: (i) a minimum reporting contract for
claim-relevant evaluation choices, (ii) controlled evidence that reasonable
scorer conventions can reverse conclusions while outputs remain fixed, and
(iii) an operational protocol for reporting results as stable, conditional,
or unresolved. This is an evaluation contribution: its primary output is an
auditable protocol supported by controlled stress tests, human-calibration
artifacts, per-cell provenance, and reusable reporting guidance.

We grade the evidence rather than imply equal validation. **Strong:**
fixed-output scorer and scorer-input analyses. **Medium:** human calibration
and the matched-context audit. **Diagnostic:** threshold, cost, retriever, and
second-generator probes. **Exploratory:** the long-form panel. Axis inclusion
indicates reporting importance, not equal empirical validation. Secondary
cells provide bounded breadth across thresholds, cost, retrieval, a second
generator, and a small long-form panel, but they are diagnostic rather than
evidence of general coverage. No modern-judge experiment was executed or is
claimed.

The framework is proposed to be procedurally portable across RAG settings;
the numerical effects observed here are not claimed to generalize beyond the
tested cells. Its implementation has two tiers. **Disclosure tier:** report
all seven categories, including “not varied” or “not measured.”
**Stress-test tier:** evaluate only reasonable alternatives capable of
changing a sign, ranking, threshold decision, or deployment choice. The
categories are practical, non-unique, and non-exhaustive; ControlledRAG does
not require a seven-dimensional factorial experiment.

**ControlledRAG in practice:** disclose all seven categories; identify
alternatives capable of changing the claim; calibrate on a
deployment-relevant human slice; stress-test only those claim-critical
alternatives; and report the conclusion as stable, conditional, or
unresolved. Disagreement is not averaged away as evaluation noise. It
identifies the assumptions on which the conclusion depends and determines
whether the claim is stable enough for publication or deployment.

The reviews led us to sharpen the paper’s central distinction: the seven-axis
framework is the methodological contribution, while the current experiments
are bounded demonstrations of why that disclosure is necessary—not equal
validation of every axis or broad numerical generalization. We have narrowed
the empirical claim, strengthened the evidence grading, and converted the
framework from a descriptive checklist into an explicit decision procedure.
The experiment map distinguishes row-reconstructable from
summary-verifiable results and does not imply universal per-query coverage.

The camera-ready will lead with a motivating decision example, define the
claim boundary and metrics before results, present one experiment map, and
separate the strongest controlled audits from bounded secondary probes. It
will also distinguish scorer disagreement from contradictory retrieved
evidence and cite Cattan et al., “DRAGged into Conflicts: Detecting and
Addressing Conflicting Sources in Search-Augmented LLMs,” arXiv:2506.08500,
2025; no contradictory-context experiment was completed.

With this narrowed claim and operational protocol, the paper provides a
bounded empirical demonstration and a reusable evaluation contribution
rather than a claim of comprehensive modern-RAG validation.
<!-- PASTE_END:area_chair -->

## Reviewer uqxN

<!-- PASTE_START:uqxN -->
Thank you for focusing on modern judges, implementation burden, and
deployment decisions. ControlledRAG applies procedurally to an LLM judge or
task-specific reward model because its identity, version, inputs, scale,
aggregation, threshold, and human calibration become explicit audit choices.
We have not empirically validated those judge families: the optional modern
judge was prepared but not executed, with zero real rows scored.

The seven categories are practical, non-unique, and non-exhaustive, and they
do not require a full factorial experiment. **Disclosure tier:** report all
seven, including “not varied” or “not measured.” **Stress-test tier:**
evaluate only reasonable alternatives capable of changing a sign, ranking,
threshold decision, or deployment choice.

**ControlledRAG in practice:** disclose all seven categories; identify
alternatives capable of changing the claim; calibrate on a
deployment-relevant human slice; stress-test only those claim-critical
alternatives; and report the conclusion as stable, conditional, or
unresolved. This is the operational answer when reasonable configurations
conflict: disagreement identifies the assumptions on which the conclusion
depends instead of being averaged away as noise.

For accuracy/robustness/cost selection, use a Pareto-first rule. Remove
systems dominated on both quality and cost, apply deployment-specific latency,
indexing, query-volume, or quality constraints to the remaining systems, and
report a conditional Pareto set when reasonable settings disagree. The
two-dataset cost audit illustrates this decision process with
hardware-specific point estimates; it does not establish a universal
economic ranking.

ControlledRAG therefore preserves full disclosure while keeping experimental
burden proportional to the strength of the claim.
<!-- PASTE_END:uqxN -->

## Reviewer wXNA

<!-- PASTE_START:wXNA -->
We agree with the distinction between measurement sensitivity and
measurement correctness. We also agree that the seven categories have uneven
empirical support and should not be presented as equally validated.

The evidence hierarchy is explicit. **Strong:** fixed-output scorer and
scorer-input analyses. **Medium:** human calibration and the matched-context
audit. **Diagnostic:** threshold, cost, retriever, and second-generator
probes. **Exploratory:** the long-form panel. Axis inclusion indicates
reporting importance, not equal empirical validation. The framework is
proposed to be procedurally portable across RAG settings; the numerical
effects observed here are not claimed to generalize beyond the tested cells.

Holding outputs and NLI backbones fixed, changing the scorer input reverses
the system comparison. On the 600-row panel, with 194 complete
baseline/HCPC-v1 pairs for each context-conditioned backbone, baseline minus
HCPC-v1 changes from `+0.017` to `-0.279` for DeBERTa and from `+0.044` to
`-0.081` for the second NLI backbone. This is fixed-output scorer-input
sensitivity, not fresh retrieval or generation.

The available human evidence gives calibration context without resolving the
requested interface comparison. On the separate `n=99` typical slice,
Spearman correlation for DeBERTa / the second NLI proxy / the RAGAS-style
judge is `0.103 / 0.394 / 0.549`; on the `n=100`
disagreement-targeted slice it is `-0.156 / 0.446 / 0.384`. On the `n=100`
binary task, average precision is `0.765 / 0.929 / 0.859`. These slices
answer different questions and are not pooled. These rows do not provide a
verified same-row human comparison between answer-only and
context-conditioned NLI.

We therefore revise the interpretation from “the context-conditioned call is
better” to “reasonable scorer interfaces can select different conclusions
and must be separately calibrated.” When baseline outperforms refinement
under an answer-only proxy but refinement outperforms baseline under
context-conditioned scoring, the correct report is not that either system
universally wins; the comparison is conditional on the scorer-input
convention.

The corrected conclusion is scorer sensitivity with slice-dependent
calibration—not universal correctness of any scorer interface.
<!-- PASTE_END:wXNA -->

## Reviewer diyB

<!-- PASTE_START:diyB -->
The empirical contribution is a controlled self-audit of RAG-faithfulness
evaluation rather than a new model or metric. The position-paper
characterization is understandable because the current organization obscured
the experiment inventory, dataset roles, and canonical artifact path.

**Primary controlled audits:** a 200-pair matched-context study; a fixed
7,500-row scorer comparison, with 2,500 rows per condition and seeds 41–45;
and a 600-row fixed-output scorer-input analysis, with 194 complete
baseline/HCPC-v1 pairs per context-conditioned backbone.

**Human and operational audits:** separate `n=99` typical and `n=100`
disagreement-targeted human slices; a five-dataset, five-threshold transfer
grid; and a two-dataset cost comparison with three systems × 200 rows per
dataset.

**Bounded breadth probes:** retriever diagnostics, including a 720-row pilot
and separate 1,200-row fixed-context re-encoding panel; one 300-row
Qwen2.5-7B probe; and a 40-question long-form panel.

The experiments answer distinct audit questions rather than form one
homogeneous benchmark: matched-context rows isolate context construction;
fixed outputs isolate scorer choice; human slices test alignment; threshold
grids test portability; and cost cells test whether quality-only rankings
survive deployment constraints. The paper does not introduce a new dataset;
existing datasets provide controlled cells for auditing RAG-faithfulness
claims.

The canonical reviewer path is the root README, the lightweight analysis
entry point, and the experiment map. Historical and recovered trees are
evidence sources, not part of the canonical execution path. The experiment
map will state dataset/split, sample size, generator, retriever/context,
scorer input, seed status, output origin, uncertainty, and evidence grade for
each cell.

The artifact map distinguishes row-reconstructable from summary-verifiable
results and labels outputs as generated, rescored, re-encoded, imported, or
aggregated. Where complete per-query rows were not included in the reviewer
artifact, we state that limitation rather than imply universal row-level
coverage.

This organization makes the empirical audit and its provenance directly
assessable without overstating its breadth or artifact completeness.
<!-- PASTE_END:diyB -->

## Reviewer d61o

<!-- PASTE_START:d61o -->
Thank you for identifying the gap between a bounded short-answer audit and
complex modern RAG. We agree: the framework’s broader applicability is a
procedural proposal, while the observed numerical effects are not established
to transfer beyond the tested cells.

For an agentic RAG system, the same disclosure structure maps naturally:
generator becomes the agent/model policy; retrieval includes search and tool
selection; context includes memory and intermediate observations;
measurement includes judge and task-success definitions; calibration uses
deployment-relevant human judgments; threshold transfer covers intervention
or abstention rules; and cost includes latency and tool calls. This is a
procedural mapping, not a claim that our measured effect sizes transfer to
agentic systems.

Operationally, define the task-level decision and endpoint, disclose all
seven practical categories, calibrate on a deployment-relevant human slice,
and stress-test reasonable choices capable of changing a sign, rank,
threshold, or deployment decision. Then report the result as stable,
conditional, or unresolved rather than compressing disagreement into a
universal score.

In a complex application, the framework succeeds only if it reveals which
conclusions remain unchanged under claim-relevant alternatives. If every
reasonable configuration selects a different system, the outcome must remain
unresolved rather than be presented as a general result. That rule makes the
procedure falsifiable at the claim level: it can withhold the conclusion when
the required stability is absent.

Existing threshold, cost, retriever, second-generator, and small long-form
cells show that the audit can be instantiated beyond one primary experiment,
but they do not constitute complex-task validation. The 40-question
long-form panel is exploratory, and the HotpotQA cost cell is not a full
multi-hop faithfulness experiment.

The evidence supports the need for the reporting procedure, while broader
complex-task effect sizes remain an explicit validation target rather than a
claim of this paper.
<!-- PASTE_END:d61o -->

## Reviewer wh9X

<!-- PASTE_START:wh9X -->
**Metrics.** The two historical NLI metrics score the answer without
retrieved context. The third scorer evaluates question, context, and answer
jointly and is a custom RAGAS-style judge, not the official `ragas` package.
Human alignment uses average precision with faithful answers as the positive
class.

**Figure 2.** The answers do not change; only the information given to the
scorer changes, and the reported system comparison reverses. For DeBERTa,
baseline minus HCPC-v1 changes from `+0.017` to `-0.279`; the second NLI
backbone shows the same directional reversal. The figure demonstrates
fixed-output scorer-input sensitivity, not fresh generation or universal
correctness.

**Why seven categories.** Each category is included because leaving it
unspecified permits a reasonable alternative choice to change the conclusion
or deployment decision. Generator means the answer process. Retrieval means
the evidence surface. Context means the evidence shown. Scorer means the
measurement. Human calibration means the interpretation. Threshold transfer
means the operational classification. Cost means the deployment choice.
These are practical, non-unique, and non-exhaustive categories. Authors
disclose all seven but stress-test only alternatives that can change the
claim; a seven-dimensional factorial experiment is not required.

**Conflicting sources.** Cattan et al., “DRAGged into Conflicts: Detecting
and Addressing Conflicting Sources in Search-Augmented LLMs,”
arXiv:2506.08500, 2025, studies contradiction among retrieved sources. Our
fixed-output result concerns scorer disagreement. These are different
phenomena, and no contradictory-context experiment was completed.

The camera-ready will use this order: motivating decision example, claim
boundary, seven-category reporting contract, plain metric definitions,
experiment map, strongest controlled audits, bounded probes, practitioner
protocol, and limitations. These changes make the inclusion criterion,
metrics, Figure 2, and relation to contradictory-source work explicit before
the experimental details.
<!-- PASTE_END:wh9X -->
