# Response to the Current/Initial AC Meta-Review

## Paste-ready response

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
