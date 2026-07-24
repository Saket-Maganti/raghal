# Meta-Review Response Map

## Provenance and disposition

The exact AC/meta-review was ingested locally and is represented here only by
precise paraphrase. AC ID: `Ji7w`. The AC gives no numerical score or
confidence value. The disposition is mixed and slightly negative: the
research direction and several audit features are valued, but the paper is
viewed as not publication-ready because clarity, accessibility, empirical
breadth, evidence balance, and practitioner guidance remain insufficient.

Realistic movement target: reduce the “not ready” assessment to a
borderline-accept or revision-remediable judgment. A stronger target is not
realistic without broader experiments.

## Positive signals to preserve

- The underlying problem—instability and under-specification in RAG
  evaluation—is considered important by most reviewers.
- The fixed-output demonstrations that scorer choice or input formatting can
  alter or reverse conclusions are viewed as valuable.
- Explicit deployment cost and reusable audit artifacts are considered
  practically relevant.
- Positive reviewer reactions include readability, transparent structure,
  and competent execution, although the AC also credits the opposing clarity
  assessments.

## Exact AC concern map

| AC item | Faithful paraphrase | Reviewer linkage | Factual misunderstanding or missing context | Valid limitation | Verified evidence available | Required response; claim ceiling | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | The abstract and introduction need a substantial accessibility rewrite suitable for a proposed standard. | `wh9X`; mixed readability reactions across reviews | No factual error to correct; this is a presentation failure. | A rebuttal cannot itself replace a full revision. | `05_clarity_material/REBUTTAL_READY_CLARITY_BLOCKS.md`; `SCOPE_AND_GENERALIZATION_STATEMENT.md` | State concrete rewrite actions: lead with problem/decision, separate method from evidence, define scope, and remove compressed shorthand. Do not claim the revision is already complete. | Critical |
| AC-02 | Metrics and experimental conventions must be defined carefully rather than assumed. | `wh9X` | The historical NLI columns may be mistaken for context-conditioned entailment unless inputs are explicit. | Exact historical package/model revisions are not locked. | `METRIC_DICTIONARY.md`; `HUMAN_EVAL_SAFE_NUMBERS.csv`; Ledger CR-003–CR-005 and CR-031–CR-040 | Define input, output, range/direction, aggregation, threshold, slice, and sklearn average-precision convention. Preserve required naming and revision caveats. | Critical |
| AC-03 | The short-answer, mostly single-hop, local-model scope leaves complex, newer, judge-based, and agentic RAG generalization uncertain. | `d61o`, `uqxN`, `wXNA` | The numerical findings were not intended to prove universal RAG behavior; the method/evidence boundary was under-explained. | No completed agentic, broad long-form, or modern-judge validation; the long-form panel is only 40 questions. | `EXPERIMENT_EVIDENCE_MATRIX.md`; `SCOPE_AND_GENERALIZATION_STATEMENT.md`; Ledger CR-002 and CR-053–CR-057 | Concede empirical scope, enumerate bounded probes, and frame broader applicability as a methodological proposal requiring future validation. Do not use HotpotQA cost cells as multi-hop faithfulness validation. | Critical |
| AC-04 | Empirical support is uneven: scorer format and human calibration are stronger than generator, retriever, and cost evidence. | `wXNA` | “Covered by the checklist” is not equivalent to “equally validated.” | Generator/retriever probes are small; cost is two-dataset, local, hardware-specific, and point-estimate based. | Evidence-strength column in `EXPERIMENT_EVIDENCE_MATRIX.md`; Ledger CR-045–CR-054 | Publish an explicit strong/medium/diagnostic/exploratory grading and scope claims to each cell. | Critical |
| AC-05 | The framework exposes conflicts but does not sufficiently tell practitioners how to interpret or aggregate them. | `uqxN`, `wXNA` | A universal scorer or scalar aggregation rule is neither established nor the safe remedy. | The decision protocol is derived from current evidence and is not prospectively validated across domains. | `CONTROLLEDRAG_DECISION_PROTOCOL.md`; `NEW_REBUTTAL_SAFE_NUMBERS.csv` | Give the stable/conditional/unresolved workflow, deployment-relevant human calibration, claim-critical stress tests, and Pareto-first cost rule. Do not declare a universal winner. | Critical |
| AC-06 | Explain the metrics, justify each Section 4 checklist entry using its inclusion rule, and add relevant work on contradictory retrieved sources. | `wh9X` | Scorer disagreement and contradictory evidence inside retrieved context are different phenomena. | The contradictory-context experiment has seeds/scripts but no completed result. | `METRIC_DICTIONARY.md`; `SEVEN_AXIS_RATIONALE.md`; local audit inventory of incomplete contradiction assets | Provide metric definitions and the seven axis-to-overclaim mappings; add the reviewer-nominated citation as related work; explicitly say no contradictory-context result is claimed. | Critical |
| AC-07 | Explain why the bounded example offers useful guidance despite limited generalizability. | `d61o` | The protocol can be instantiated outside the tested cells even though the observed numerical effects cannot be exported. | Complex-task empirical validation remains missing. | `SCOPE_AND_GENERALIZATION_STATEMENT.md`; `CONTROLLEDRAG_DECISION_PROTOCOL.md`; `EXPERIMENT_EVIDENCE_MATRIX.md` | Separate methodological portability from numerical generalization and give an operational instantiation procedure. | Critical |
| AC-08 | Clarify the empirical contribution, codebase, datasets, and experiment descriptions. | `diyB` | “Position paper only” omits the empirical audit inventory; however, navigation and provenance shortcomings are real. | Some full rows are recovered, the submitted artifact is not universally complete, and exact historical environments are unlocked. | `EXPERIMENT_EVIDENCE_MATRIX.md`; `FULL_PER_QUERY_PROVENANCE_REPORT.md`; Ledger (56 verified of 62, with exclusions); `P0_INTEGRITY_GATE.md` | Provide one canonical experiment/artifact map and accurate output-origin labels. Never call recovered material submitted or claim complete per-query coverage. | Critical |

## Response order

1. Lead with claim narrowing and the method-versus-evidence boundary
   (AC-03, AC-04, AC-07).
2. Repair accessibility and experimental definitions (AC-01, AC-02, AC-06).
3. Provide the practitioner decision protocol (AC-05).
4. Give the empirical/code/data inventory and provenance caveats (AC-08).
5. Close with concrete revision commitments and unresolved future validation,
   without promising new results.

## AC-safe synthesis boundary

The strongest defensible synthesis is that the package empirically
demonstrates measurement sensitivity and conditional decisions in bounded
cells, while the seven-axis framework is a practical disclosure proposal.
It is unsafe to claim broad empirical validation, equal support for all axes,
a universally correct scorer, a completed modern-judge experiment, or
complete submitted per-query coverage.
