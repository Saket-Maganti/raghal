# Reviewer Concern Matrix

## Source status

Exact review records found: **0 of 5**.

Exact AC/meta-review records found: **0 of 1**.

The search covered the four source trees, the ingest repository audit
materials, and the local rebuttal prompt pack. A pre-existing sanitized
thematic audit contains 14 reviewer/meta-review concern clusters, but it does
not preserve reviewer IDs, scores, confidence values, direct questions,
positive comments, or concern-to-reviewer attribution. Because the repository
is public, this file would use sanitized paraphrases even if exact review text
were available.

## Required five-review slots

| Reviewer slot | Reviewer ID | Score | Confidence | Positive comments | Weaknesses/questions | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | `SOURCE_MISSING` | `SOURCE_MISSING` | `SOURCE_MISSING` | `SOURCE_MISSING` | Cannot attribute thematic concerns without the review export | Blocked |
| R2 | `SOURCE_MISSING` | `SOURCE_MISSING` | `SOURCE_MISSING` | `SOURCE_MISSING` | Cannot attribute thematic concerns without the review export | Blocked |
| R3 | `SOURCE_MISSING` | `SOURCE_MISSING` | `SOURCE_MISSING` | `SOURCE_MISSING` | Cannot attribute thematic concerns without the review export | Blocked |
| R4 | `SOURCE_MISSING` | `SOURCE_MISSING` | `SOURCE_MISSING` | `SOURCE_MISSING` | Cannot attribute thematic concerns without the review export | Blocked |
| R5 | `SOURCE_MISSING` | `SOURCE_MISSING` | `SOURCE_MISSING` | `SOURCE_MISSING` | Cannot attribute thematic concerns without the review export | Blocked |
| AC/meta-review | `SOURCE_MISSING` | n/a | n/a | `SOURCE_MISSING` | Cannot distinguish AC priorities from reviewer themes | Blocked |

No realistic score movement is estimated without the actual scores and review
language.

## Sanitized thematic concern clusters

These clusters are not assigned to a reviewer. “Submitted” means evidence
inside the immutable submitted artifact; “recoverable” means candidate
evidence outside it that still needs Prompt 02 provenance validation.

| Theme | Sanitized weakness or question | Factual misunderstanding | Valid limitation | Evidence already submitted | Recoverable evidence | Clarification-only answer | Existing-output analysis | Optional new experiment | Realistic score movement | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 Empirical scope | Does the evidence generalize beyond narrow short-answer QA and 7B-class generators? | Treating the paper as claiming universal RAG generalization would exceed its stated scope. | Most audited cells are SQuAD/PubMedQA and 7B-class. | Main-paper limitations; Qwen probe; retriever and long-form summaries. | Full Qwen/long-form per-query files. | State that the contribution is a bounded audit methodology, not universal empirical coverage. | Add uncertainty and a coverage matrix from fixed outputs. | Preregister a multi-generator, multi-dataset replication. | Unknown without review source. | High |
| C02 Short-answer/single-hop dependence | Is the method supported on multi-hop or long-form synthesis? | HotpotQA cost cells are not a full multi-hop faithfulness validation. | Long-form probe is only 40 questions. | QASPER/MS-MARCO summaries and HotpotQA cost table. | Full long-form per-query file. | Describe the long-form evidence as exploratory and non-confirmatory. | Bootstrap the 40 fixed-output rows after provenance validation. | Powered multi-hop/long-form run with claim-level scoring. | Unknown. | High |
| C03 Modern/task-specific judges | Why are newer judges or task-specific evaluators absent? | Recent frameworks are discussed, not run. | Frozen evaluation uses two legacy proxies and one local RAGAS-style judge. | Scorer definitions and human calibration. | Context-conditioned outputs and candidate fixed rows. | Separate related-work coverage from executed evaluators. | Reformat current results by input format and human slice. | Optional pre-hashed fixed-sample modern judge; rebuttal must not depend on it. | Unknown. | High |
| C04 Uneven seven-axis evidence | Are all seven axes supported equally? | “Exercised” does not mean equal evidence strength. | Generator, long-form, cost, and retriever probes are weaker than scorer/context/human evidence. | Filled reporting checklist and discussion strength tags. | Per-query files for selected weak cells. | Label each axis strong, medium/diagnostic, or weak/exploratory with `n`. | Build a coverage matrix with source hashes. | Fill only the highest-value empty cell after provenance work. | Unknown. | High |
| C05 Practitioner guidance | Which scorer/configuration should a practitioner trust when metrics disagree? | The paper does not validate a universal winner. | No prospectively validated decision rule exists. | Checklist, slice-dependent human results, cost table. | Existing fixed outputs for a conservative decision table. | Recommend multi-scorer reporting plus human calibration, not one universal scorer. | Build a conditional guidance table keyed by context, calibration, thresholds, and cost. | Validate guidance prospectively on a held-out dataset. | Unknown. | Medium |
| C06 Metric clarity | Are scorer inputs, thresholds, scales, and AUPRC definitions clear? | Native scorer values are not directly comparable. | Cleanup and submitted AUPRC implementations conflict. | Main/supplement metric definitions and submitted script. | Historical script/output only as conflict evidence. | Define input format, direction, aggregation, threshold, slice, and submitted AUPRC convention compactly. | Recompute displayed values from the submitted implementation in Prompt 02. | None needed unless a new judge is added. | Unknown. | Critical |
| C07 Exactly seven axes | Why seven rather than six or eight? | Seven is not mathematically unique or exhaustive. | The taxonomy is justified conceptually, not by an exhaustive proof. | “Reasonable substitution can change the conclusion” criterion. | Candidate axis-to-effect mapping. | Present seven as a minimum disclosure decomposition for this audit. | Map each axis to an observed sensitivity and note possible omissions. | Empirical study of checklist completeness across papers. | Unknown. | High |
| C08 Dataset/experiment description | Can every result be identified by split, `n`, model, retriever, scorer input, seed, and operation type? | Re-encoding is not fresh end-to-end generation/retrieval. | Several full per-query inputs are absent from the submitted artifact. | README, source trace, claims audit, manifests. | Full cleanup per-query files and process notes. | Label each row generated, rescored, re-encoded, imported, or summary-only. | Complete the claim-to-evidence ledger and provenance checks. | None until trace gaps are understood. | Unknown. | Critical |
| C09 Code navigation | Is the artifact too difficult to navigate or execute? | The canonical reviewer artifact is smaller than the historical/remnant trees. | Four optional scripts have syntax errors; source trace overstates default regeneration. | Reviewer README, reproduce guide, entry point, trace docs. | Historical tree aids forensic reconstruction only. | Direct reviewers to the submitted artifact and lightweight path. | No new science analysis required. | Later repair branch with locked environment and canonical map. | Unknown. | High |
| C10 Conflicting retrieved evidence | Is there an experiment with contradictory evidence in context? | Scorer disagreement is not conflicting retrieved evidence. | Seeds/scripts exist, but no completed result was found. | Contradiction seed data and experimental scripts only. | Same seeds/scripts in cleanup snapshots. | Explicitly say this experiment is absent and do not conflate concepts. | Validate seed construction/provenance without claiming outcomes. | Run coherent controls and contradictory contexts after rebuttal if authorized. | Unknown. | Medium |
| C11 Scorer input format/human calibration | Why do scorer rankings differ, and how does context conditioning matter? | Context-conditioned NLI is not universally correct. | `n=600` is a subset; human calibration is slice-specific. | Fixed-row rescoring and two human slices. | Full fixed-row inputs may support deeper checks. | Put scorer inputs and slice construction beside each result. | Add paired uncertainty and verify fixed-row alignment. | Same fixed sample under matched answer-only/context-conditioned judge formats. | Unknown. | Critical |
| C12 Annotation provenance | Were annotations independent, reconciled, and consistently defined? | The two slices use different label schemas and answer different questions. | Two raters are not a broad annotator pool. | Separate rater files, adjudication files, summaries. | Cleanup copies can establish version identity only. | State author-confirmed independence, later adjudication, and use pre-adjudication labels for agreement. | Verify IDs, missingness, label transforms, and separate analyses. | No new annotation unless provenance fails. | Unknown. | Critical |
| C13 Publication/privacy safety | Does the package expose identities, credentials, or executable prompt injection? | Scientific mentions of “system prompt” are not executable instructions. | Target repository is public and source history has identifying material. | Public-safety audit and exclusion manifests. | None needed for science. | Keep exact reviews and identifying metadata out of this public repository. | Repeat scoped secret/privacy scans before each commit. | None. | Unknown. | Critical |
| C14 Missing per-query/source trace | Can headline summaries be reconstructed independently? | Presence of a remnant file alone does not prove provenance. | Submitted artifact has only one `*per_query*` file. | Frozen summaries, one compact per-query file, scripts/docs. | 127 per-query paths in cleanup pre-cleanup material. | Distinguish summary-verifiable from row-reconstructable claims. | Hash and trace highest-priority per-query inputs in Prompt 02. | None unless a generating run is genuinely missing. | Unknown. | Critical |

## Unavailable reviewer-specific fields

Direct questions, positive comments, per-review factual misunderstandings,
reviewer-specific evidence, reviewer-specific response priority, and score
movement remain blocked. They must be filled from a supplied review export,
without storing verbatim text while the repository is public.
