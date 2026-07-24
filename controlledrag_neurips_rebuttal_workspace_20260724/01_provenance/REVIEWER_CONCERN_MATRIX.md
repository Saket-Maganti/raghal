# Reviewer Concern Matrix

## Source and handling status

All five reviewer records and the AC/meta-review were ingested from the
author-supplied local review export. The confidential source remains outside
this Git repository. This matrix preserves reviewer IDs, ratings, confidence
values, and precise concern-level paraphrases; it does not reproduce review
prose, timestamps, or other unnecessary metadata.

Coverage: **5/5 reviewers** and **1/1 AC/meta-review**. Direct response items
are enumerated in `06_reviewer_responses/DIRECT_QUESTION_CHECKLIST.md`.

## Reviewer-level map

| Reviewer | Score | Confidence | Positive assessment, paraphrased | Main weaknesses, paraphrased | Factual misunderstanding or missing context | Valid limitations to concede | Response priority | Realistic movement target |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| `uqxN` | 5 | 4 | Values the systematic audit, the fixed-output scorer-format reversal, the reusable seven-axis evidence package, reproducibility, and explicit cost reporting. | Breadth beyond the tested retrieval-refinement settings is unclear; seven-axis use may be burdensome; the paper needs an operational rule for conflicting evaluations and accuracy/robustness/cost trade-offs. | Full seven-axis disclosure does **not** require a full factorial experiment: the protocol asks authors to disclose all axes and stress-test only claim-critical alternatives. | No completed modern-judge or reward-model validation; bounded datasets/models; no prospectively validated universal aggregation rule. | Medium—protect an existing accept and answer every operational question. | Preserve 5; a higher score is possible but should not be planned on. |
| `wXNA` | 4 | 1 | Finds the framework actionable, the fixed-output scorer-format result compelling, the negative findings candid, and the experimental/statistical separation relatively transparent. | Evidence depth is uneven; the main scope is narrow; the sign reversal must not be interpreted as proving the alternative scorer correct; human comparisons should guide scorer disagreement. | No material factual error. The review correctly distinguishes sensitivity from correctness. It does, however, omit some bounded breadth outside the main SQuAD cells: a five-dataset threshold grid, two-dataset cost audit, retriever diagnostics, one Qwen probe, and a small long-form panel. | Generator/retriever/cost evidence is weaker than scorer/context/human evidence; only one additional local generator; cost is local and hardware-specific; human slices are small and non-poolable. | High—low confidence and an already-positive score make a precise clarification valuable. | Preserve 4; 4→5 is plausible if caution, evidence grading, and guidance are convincing. |
| `diyB` | 2 | 3 | Sees the core idea as interesting. | Reads the work as position-like and methodologically thin; cannot identify the experiment inventory, dataset roles, or canonical code path. | “Position paper only” is factually incomplete: the package contains empirical matched-context, scaled fixed-output scorer, human-calibration, threshold, cost, retriever, second-generator, and exploratory long-form audits. The navigation criticism remains credible because historical/recovered trees and incomplete submitted per-query coverage complicate reconstruction. | Empirical coverage is bounded and uneven; several inputs are recovered rather than submitted; exact historical model/package revisions are not locked; universal artifact-completeness claims are unsafe. | Critical—the AC explicitly requests a response to this review. | Aim for 2→3; a larger move is unrealistic without new broad experiments. |
| `d61o` | 3 | 4 | Regards reporting standardization as important, believes the seven categories capture essential factors, considers the work competent/readable, and views it as publishable in principle; also finds the repository organized. | The short-answer, mostly single-hop demonstration is too simple to establish generalizability to more complex modern RAG. | The methodological standard is proposed for broader use, but the paper must not imply that its numerical effects generalize broadly. The bounded evidence does include more than the three headline QA datasets, but none of those probes constitutes large-scale complex-task validation. | Primary empirical scope is short-answer QA with 7B-class local models; long-form evidence is only 40 questions; HotpotQA cost cells are not a full multi-hop faithfulness validation. | Critical—the AC identifies generalizability as a primary concern and names this review. | Aim for 3→4 by narrowing claims and showing concrete applicability guidance; 3→5 is not realistic. |
| `wh9X` | 1 | 3 | Agrees that entanglement among evaluation choices is important. | Metrics and Figure 2 are not accessible; the seven checklist entries are not justified against the stated inclusion rule; experiment organization is difficult to follow; relevant conflicting-source work is missing; requests a substantial rewrite. | These are principally clarity and presentation failures, not evidence that the calculations are wrong. The seven-axis rationale and Figure 2 mechanism can be made explicit, but the rebuttal cannot claim the submitted presentation was already clear. | A rebuttal cannot itself deliver a full paper rewrite; contradictory retrieved evidence was not completed as an experiment; only a related-work addition and a clear distinction from scorer disagreement are safe. | Critical—the AC expressly incorporates this review’s clarity, metric, checklist, and citation concerns. | Aim for 1→2 by demonstrating concrete corrections; 1→3 is possible only if the reviewer accepts substantial revision commitments. |

## Concern-to-evidence map

Evidence abbreviations: `P0` =
`01_provenance/P0_INTEGRITY_GATE.md`; `Ledger` =
`01_provenance/CLAIM_TO_EVIDENCE_LEDGER.csv`; `Human` =
`02_human_eval/HUMAN_EVAL_SAFE_NUMBERS.csv`; `New` =
`03_existing_analyses/NEW_REBUTTAL_SAFE_NUMBERS.csv`; `Matrix` =
`05_clarity_material/EXPERIMENT_EVIDENCE_MATRIX.md`; `Metrics` =
`05_clarity_material/METRIC_DICTIONARY.md`; `Protocol` =
`05_clarity_material/CONTROLLEDRAG_DECISION_PROTOCOL.md`.

| Concern ID | Reviewer | Sanitized weakness or question | Direct-item IDs | Verified evidence available | Safe response and claim ceiling | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| UQ-01 | `uqxN` | How far do the findings extend to current LLM judges or task-specific reward models? | UQ-Q1 | The executed scorer set, two separate human slices, and fixed-output scorer-format analysis are in `Matrix`; `Human` and `New` quantify slice-dependent alignment. The optional modern-judge package is `PREPARED_NOT_EXECUTED`, with zero real rows. | Acknowledge this as untested. Explain that the protocol applies conceptually, but do not imply a modern-judge result or broad empirical validation. | High |
| UQ-02 | `uqxN` | Can the framework be simplified, and what overhead is actually required? | UQ-Q2 | `Protocol` steps 2 and 6 and `SEVEN_AXIS_RATIONALE.md` separate mandatory disclosure from claim-critical stress tests. | Clarify “disclose all; vary only claim-critical alternatives.” Do not call seven unique or exhaustive (`Ledger` CR-001; `P0`). | High |
| UQ-03 | `uqxN` | What should practitioners do when reasonable configurations conflict, and how should accuracy, robustness, and cost be balanced? | UQ-Q3 | `Protocol` defines stable/conditional/unresolved classes and a Pareto-first rule; `New` records conditional two-dataset frontiers and weight sensitivity. | Give the decision protocol, not a universal aggregation formula. Cost conclusions remain two-dataset, hardware-specific point-estimate sensitivities. | High |
| WX-01 | `wXNA` | Evidence is uneven across the seven axes, especially generator, retriever, and cost. | WX-Q1 | `Matrix` grades scorer-format strong, human/context medium, and generator/retriever/long-form exploratory; `Ledger` CR-045–CR-057 states each boundary. | Concede and label evidence strength by cell. “Exercised” must not be rewritten as “equally validated.” | Critical |
| WX-02 | `wXNA` | Main datasets/models and the matched-context audit are narrow. | WX-Q2 | `Matrix` records the primary SQuAD/7B cells plus bounded five-dataset threshold, HotpotQA cost, Qwen, retriever, and 40-question long-form probes. | Scope numerical findings to tested cells. Use bounded breadth only to show diagnostics, never broad generalization (`Ledger` CR-002, CR-053–CR-057; `P0`). | Critical |
| WX-03 | `wXNA` | The sign reversal demonstrates scorer-input sensitivity, not that context-conditioned NLI is more correct; scorer formats should be compared with humans and disagreements interpreted cautiously. | WX-Q3 | `New` gives paired input-format contrasts and CIs; `Human` gives separate slice-specific alignment for the two legacy proxies and RAGAS-style judge; `Protocol` classifies scorer ordering as conditional. There is no verified same-row human comparison of answer-only versus context-conditioned NLI. | Agree explicitly and mark the requested matched human comparison as missing. Never call context-conditioned NLI universally correct, never pool human slices, and do not compare native scorer scales as commensurate. | Critical |
| DY-01 | `diyB` | The work appears position-like rather than an empirical contribution with verified claims. | — | `Matrix` inventories ten empirical questions; `Ledger` contains 56 verified claims out of 62, with mismatches quarantined by `P0`. | Correct the empirical inventory while conceding narrowness. Do not claim all original headline statements or complete per-query coverage are verified. | Critical |
| DY-02 | `diyB` | Clearly enumerate how experiments were run and describe the data and canonical artifact path. | DY-Q1 | `Matrix` lists dataset/split, sample size, generator, retriever/context, scorer input, seed, origin, uncertainty, strength, and source; `METRIC_DICTIONARY.md` defines endpoints; `FULL_PER_QUERY_PROVENANCE_REPORT.md` distinguishes submitted/recovered/aggregated outputs. | Provide a compact experiment map and canonical navigation path. Label generated, rescored, re-encoded, imported, or aggregated outputs accurately; never call recovered rows submitted. | Critical |
| D6-01 | `d61o` | Does the simple short-answer/single-hop example justify applicability in complex modern RAG? | D6-Q1 | `SCOPE_AND_GENERALIZATION_STATEMENT.md` separates method applicability from numerical generalization; `Matrix` records the bounded probes and their grades. | Concede that complex/agentic validation remains future work. Explain why the disclosure procedure transfers as a method without asserting that observed effect sizes transfer. | Critical |
| D6-02 | `d61o` | The paper needs concrete guidance for applying the framework in more complex settings. | D6-Q1 | `Protocol` supplies a ten-step workflow, decision classes, calibration rule, and Pareto rule. | Describe how to instantiate task-specific axes/endpoints and narrow unresolved claims; do not present the protocol as prospectively validated across agentic tasks. | High |
| WH-01 | `wh9X` | Metric names, inputs, directions, aggregation, and thresholds are too compressed to assess. | WH-Q1 | `Metrics` defines every used metric in plain language and locks required naming; `Human` locks sklearn average precision and endpoints. | Answer with definitions and commit to rewriting setup prose. Use “legacy answer-only zero-shot label proxy,” “RAGAS-style,” and “average precision” exactly as locked. | Critical |
| WH-02 | `wh9X` | Figure 2 is not interpretable from the paper. | WH-Q2 | `FIGURE_2_PLAIN_LANGUAGE_EXPLANATION.md`; `New` gives `+0.017→-0.279` and `+0.044→-0.081` with paired intervals on 194 complete pairs. | Explain same fixed outputs/backbones, different scorer inputs, opposite contrast direction. This is fixed-output sensitivity, not fresh RAG execution or scorer correctness. | Critical |
| WH-03 | `wh9X` | The seven entries are not individually justified by the checklist inclusion criterion. | WH-Q3 | `SEVEN_AXIS_RATIONALE.md` maps each category to its distinct question, evidence, and blocked overclaim; `Ledger` CR-001 constrains the framework claim. | Give the axis-to-criterion mapping. Describe the list as a practical minimum for this audit, not mathematically unique or exhaustive. | Critical |
| WH-04 | `wh9X` | Related work should cover conflict among retrieved sources. | WH-Q4 | The audit inventory contains contradiction seeds/scripts but no completed result; `P0` prevents inventing an outcome. | Add and discuss the reviewer-nominated conflicting-source work, while explicitly distinguishing contradictory retrieved content from scorer disagreement. Do not claim the missing experiment was run. | High |
| WH-05 | `wh9X` | Abstract, introduction, setup, figure explanation, and experiment organization need substantial rewriting. | WH-Q5 | `REBUTTAL_READY_CLARITY_BLOCKS.md`, `Metrics`, `Matrix`, and the Figure 2 explanation provide verified rewrite material. | Commit to specific structural revisions. Do not claim a full rewrite has already been completed in the rebuttal workspace. | Critical |

## Shared integrity constraints

Every response must preserve the following prior-handoff constraints:

- use only ledger rows marked `VERIFIED_EXACT`,
  `VERIFIED_WITH_ROUNDING`, or `VERIFIED_SUMMARY_ONLY`, within each row’s
  safety language;
- never use stale average-precision values or the unreproduced matched
  `p=0.011`;
- keep the `n=99` and `n=100` human slices separate;
- describe fixed-context work as rescoring or re-encoding, not fresh
  retrieval/generation;
- do not claim context-conditioned NLI is universally correct;
- do not claim the seven axes are unique or exhaustive;
- do not broaden bounded Qwen, retriever, long-form, threshold, or cost probes
  into universal evidence;
- do not claim a modern-judge result: the package is prepared but unexecuted;
- do not claim universal per-query artifact completeness, immutable
  preregistration timing, compensation, IRB status, or exact historical
  package/model revisions; and
- do not conflate conflicting retrieved evidence with scorer disagreement.
