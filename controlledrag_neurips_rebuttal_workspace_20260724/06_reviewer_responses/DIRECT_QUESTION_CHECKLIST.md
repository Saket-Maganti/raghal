# Direct Question Checklist

## Handling rule

This checklist is a sanitized response-control artifact, not a transcript.
Each item is a precise paraphrase of an explicit question, requested
clarification, or—where the source’s question field points back to the
weakness section—the incorporated actionable request. No final response is
drafted here.

Status vocabulary: `MAPPED` means evidence and a safe response boundary are
identified; it does not mean rebuttal prose has been written.

## Area Chair `Ji7w`

| Item | Direct response obligation, paraphrased | Evidence / response source | Required caveat | Status |
| --- | --- | --- | --- | --- |
| AC-Q1 | Explain how the abstract and introduction will be made accessible to a broader audience. | `REBUTTAL_READY_CLARITY_BLOCKS.md`; `SCOPE_AND_GENERALIZATION_STATEMENT.md` | Commit to concrete revision actions; do not say a full rewrite is already complete. | MAPPED |
| AC-Q2 | Define the metrics and conventions carefully. | `METRIC_DICTIONARY.md`; `HUMAN_EVAL_SAFE_NUMBERS.csv` | Preserve locked scorer names, input formats, slice labels, and sklearn AP convention. | MAPPED |
| AC-Q3 | Address the narrow short-answer/single-hop, local-model scope and uncertainty for modern judges or agentic/complex RAG. | `EXPERIMENT_EVIDENCE_MATRIX.md`; `SCOPE_AND_GENERALIZATION_STATEMENT.md` | Method portability is a proposal; numerical generalization is not established. | MAPPED |
| AC-Q4 | Distinguish stronger axes from weak or exploratory axes. | Evidence grades in `EXPERIMENT_EVIDENCE_MATRIX.md` | Do not imply equal validation across all seven axes. | MAPPED |
| AC-Q5 | Give practitioners a procedure for conflicting outcomes. | `CONTROLLEDRAG_DECISION_PROTOCOL.md` | No universal scorer, aggregate, or cost winner is validated. | MAPPED |
| AC-Q6 | Respond to the metric, checklist-criteria, and conflicting-source citation issues associated with `wh9X`. | `METRIC_DICTIONARY.md`; `SEVEN_AXIS_RATIONALE.md`; incomplete contradiction-assets inventory | Add related work, but do not claim a contradictory-context result. | MAPPED |
| AC-Q7 | Respond to `d61o` on generalizability and applicability to complex settings. | `SCOPE_AND_GENERALIZATION_STATEMENT.md`; `CONTROLLEDRAG_DECISION_PROTOCOL.md` | Concede missing complex-task validation. | MAPPED |
| AC-Q8 | Respond to `diyB` with a clear code, dataset, and experiment map. | `EXPERIMENT_EVIDENCE_MATRIX.md`; `FULL_PER_QUERY_PROVENANCE_REPORT.md` | Preserve submitted/recovered/rescored/re-encoded distinctions. | MAPPED |

## Reviewer `uqxN` — score 5, confidence 4

| Item | Direct question, paraphrased | Evidence / response source | Required caveat | Status |
| --- | --- | --- | --- | --- |
| UQ-Q1 | How well do the findings extend to LLM judges or task-specific reward models? | Current scorer/human rows in `EXPERIMENT_EVIDENCE_MATRIX.md`; modern-judge `STATUS.md` | The optional package is prepared but unexecuted; no such result exists. | MAPPED |
| UQ-Q2 | Can seven axes be reduced to a smaller robust set without losing diagnostic value? | `SEVEN_AXIS_RATIONALE.md`; steps 2 and 6 of `CONTROLLEDRAG_DECISION_PROTOCOL.md` | Seven is a practical minimum here, not unique or exhaustive; disclosure is not full-factorial testing. | MAPPED |
| UQ-Q3 | How should real deployments balance accuracy, robustness, and cost when reasonable configurations disagree? | Decision classes and Pareto rule in `CONTROLLEDRAG_DECISION_PROTOCOL.md`; conditional frontiers in `NEW_REBUTTAL_SAFE_NUMBERS.csv` | The audited cost result is two-dataset, hardware-specific, and point-estimate based. | MAPPED |

## Reviewer `wXNA` — score 4, confidence 1

The source question field contains no standalone interrogative and explicitly
incorporates the weakness section. The three actionable requests below cover
that incorporated question in full.

| Item | Incorporated question/request, paraphrased | Evidence / response source | Required caveat | Status |
| --- | --- | --- | --- | --- |
| WX-Q1 | How should readers interpret the uneven support for generator, retriever, and cost axes? | Strength grades in `EXPERIMENT_EVIDENCE_MATRIX.md`; Ledger CR-045–CR-054 | Label weak cells as diagnostic/exploratory. | MAPPED |
| WX-Q2 | How far can the SQuAD/short-answer/7B-centered findings generalize? | `SCOPE_AND_GENERALIZATION_STATEMENT.md`; bounded breadth rows in the experiment matrix | Do not promote Qwen, retriever, threshold, cost, or 40-question long-form probes into broad validation. | MAPPED |
| WX-Q3 | What does the sign reversal establish, how do scorer formats align with humans, and what should happen when they disagree? | `NEW_REBUTTAL_SAFE_NUMBERS.csv`; partial scorer evidence in `HUMAN_EVAL_SAFE_NUMBERS.csv`; decision protocol | Sensitivity is not correctness; no verified same-row answer-only-versus-context-conditioned human comparison exists; keep `n=99` and `n=100` separate; no universal scorer winner. | MAPPED |

## Reviewer `diyB` — score 2, confidence 3

| Item | Direct question, paraphrased | Evidence / response source | Required caveat | Status |
| --- | --- | --- | --- | --- |
| DY-Q1 | Clearly list how every experiment was run and describe the datasets/data path in the paper and codebase. | `EXPERIMENT_EVIDENCE_MATRIX.md`; `METRIC_DICTIONARY.md`; `FULL_PER_QUERY_PROVENANCE_REPORT.md` | Do not call recovered rows submitted or claim complete per-query artifact coverage. | MAPPED |

The accompanying “position paper” concern is mapped as DY-01 in
`REVIEWER_CONCERN_MATRIX.md` even though it is not phrased as a question.

## Reviewer `d61o` — score 3, confidence 4

| Item | Direct question, paraphrased | Evidence / response source | Required caveat | Status |
| --- | --- | --- | --- | --- |
| D6-Q1 | Does the bounded example provide enough guidance to apply the framework in more complex settings? | `SCOPE_AND_GENERALIZATION_STATEMENT.md`; `CONTROLLEDRAG_DECISION_PROTOCOL.md`; experiment matrix | Distinguish procedural applicability from unproven numerical generalization. | MAPPED |

## Reviewer `wh9X` — score 1, confidence 3

The source question field requests a major rewrite rather than posing a
standalone interrogative. The request and every actionable issue it
incorporates are tracked below.

| Item | Direct request, paraphrased | Evidence / response source | Required caveat | Status |
| --- | --- | --- | --- | --- |
| WH-Q1 | Rewrite metric descriptions so their inputs, outputs, direction, aggregation, and thresholds are understandable. | `METRIC_DICTIONARY.md` | Exact historical package/model revisions remain unlocked. | MAPPED |
| WH-Q2 | Explain Figure 2 plainly. | `FIGURE_2_PLAIN_LANGUAGE_EXPLANATION.md`; paired contrasts in `NEW_REBUTTAL_SAFE_NUMBERS.csv` | Fixed-output sensitivity only; not fresh retrieval/generation or a proof of correctness. | MAPPED |
| WH-Q3 | Justify each checklist entry using the stated inclusion criterion. | `SEVEN_AXIS_RATIONALE.md` | Do not call seven mathematically unique or exhaustive. | MAPPED |
| WH-Q4 | Add and discuss the nominated related work on conflicting retrieved sources. | Related-work revision task; incomplete contradiction-assets inventory | Scorer disagreement is not contradictory retrieved content; no completed contradiction result exists. | MAPPED |
| WH-Q5 | Substantially reorganize the abstract, introduction, setup, and experiment presentation. | Clarity blocks, metric dictionary, experiment matrix, scope statement | The rebuttal can specify planned revisions but cannot claim the full paper is already rewritten. | MAPPED |

## Coverage verification

- AC obligations: 8/8 mapped.
- `uqxN`: 3/3 direct questions mapped.
- `wXNA`: the referenced weakness section is covered by 3/3 incorporated
  requests.
- `diyB`: 1/1 direct question mapped.
- `d61o`: 1/1 direct question mapped.
- `wh9X`: the rewrite request and 4/4 incorporated actionable issues are
  mapped.
- Unanswered or unmapped direct items: **0**.
- Final reviewer-specific response text drafted: **no**, by instruction.
