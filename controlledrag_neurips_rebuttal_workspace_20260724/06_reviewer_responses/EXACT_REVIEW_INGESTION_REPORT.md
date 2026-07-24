# Exact Review Ingestion Report

## Outcome

Status: `EXACT_REVIEWS_INGESTED_SANITIZED`

The author-supplied local source was read in full. Five reviewer records and
one AC/meta-review record were mapped into the public-safe rebuttal workspace.
The confidential source is outside the Git root and is not part of the
commit. No final rebuttal or reviewer-response prose was drafted.

## Metadata verification

| Role | ID | Score | Confidence | Verified |
| --- | --- | ---: | ---: | --- |
| Reviewer | `uqxN` | 5 | 4 | Yes |
| Reviewer | `wXNA` | 4 | 1 | Yes |
| Reviewer | `diyB` | 2 | 3 | Yes |
| Reviewer | `d61o` | 3 | 4 | Yes |
| Reviewer | `wh9X` | 1 | 3 | Yes |
| Area chair | `Ji7w` | Not supplied | Not supplied | Yes |

Reviewer score cross-check: mean `3.0`, median `3`, range `1–5`.

## Field coverage

| Required field | Coverage | Location |
| --- | --- | --- |
| Reviewer IDs | 5/5 | `01_provenance/REVIEWER_CONCERN_MATRIX.md` |
| Scores | 5/5 | Reviewer matrix; this report |
| Confidence values | 5/5 | Reviewer matrix; this report |
| Positive comments | 5/5 reviewers plus AC positive signals | Reviewer matrix; `META_REVIEW_RESPONSE_MAP.md` |
| Weaknesses | All reviewer and AC concern clusters mapped | Reviewer and meta-review maps |
| Direct questions/requests | 8 AC obligations; 3 `uqxN`; 3 incorporated `wXNA`; 1 `diyB`; 1 `d61o`; 5 `wh9X` requests/issues | `DIRECT_QUESTION_CHECKLIST.md` |
| Factual misunderstandings or missing context | 5/5, including explicit “none” where the criticism is accurate | Reviewer matrix |
| Valid limitations | 5/5 and all AC items | Reviewer and meta-review maps |
| Evidence available | Concern-level source mapping complete | Reviewer and meta-review maps |
| Response priority | Reviewer-level and concern-level | Reviewer and meta-review maps |
| Realistic score movement | 5/5; qualitative AC target | Reviewer and meta-review maps |

The `wXNA` question field refers to the weakness section rather than supplying
a separate interrogative. The checklist therefore tracks all three
actionable weakness requests. The `wh9X` question field requests a major
rewrite; the checklist tracks that request and its four incorporated
actionable issues. This preserves complete question coverage without
inventing source wording.

## Evidence cross-check

The concern maps were checked against all required control files:

- `01_provenance/P0_INTEGRITY_GATE.md`;
- `01_provenance/CLAIM_TO_EVIDENCE_LEDGER.csv`;
- `02_human_eval/HUMAN_EVAL_SAFE_NUMBERS.csv`;
- `03_existing_analyses/NEW_REBUTTAL_SAFE_NUMBERS.csv`;
- `05_clarity_material/EXPERIMENT_EVIDENCE_MATRIX.md`;
- `05_clarity_material/METRIC_DICTIONARY.md`;
- `05_clarity_material/CONTROLLEDRAG_DECISION_PROTOCOL.md`; and
- prior handoff constraints in `PROMPT_01_HANDOFF.md`,
  `PROMPT_02_HANDOFF.md`, `PROMPT_03_HANDOFF.md`,
  `PROMPT_04_HANDOFF.md`, `PROMPT_05_HANDOFF.md`, and
  `PROMPT_05_REPAIR_HANDOFF.md`.

Ledger status at ingestion: 62 claims total; 2
`VERIFIED_SUMMARY_ONLY`, 4 `VERIFIED_EXACT`, 50
`VERIFIED_WITH_ROUNDING`, 4 `MISMATCH`, 1
`PROVENANCE_MATCH_PENDING`, and 1 `NOT_REBUTTAL_SAFE`. Only the 56 verified
rows may be used, and only within their row-specific safety language.

## Key adjudications

| Review concern | Ingestion adjudication |
| --- | --- |
| Broad generalization | Valid limitation. The method can be proposed more broadly, but numerical findings remain bounded to tested cells. |
| Uneven support across seven axes | Valid limitation. Scorer-format evidence is strongest; generator, retriever, cost, and long-form evidence must be graded as diagnostic or exploratory. |
| “Position paper only” | Factually incomplete. The package contains multiple empirical audits, but navigation, scope, and provenance limitations remain valid. |
| Scorer sign reversal | Supports measurement sensitivity only. It does not establish that context-conditioned NLI is universally correct. |
| Human calibration | Evidence exists for the legacy proxies and RAGAS-style judge, but not for a same-row answer-only-versus-context-conditioned NLI comparison. The `n=99` typical and `n=100` disagreement-targeted slices also have different designs/schemas and cannot be pooled. |
| Modern judges | Valid missing validation. The optional package is prepared but unexecuted; zero real results may be claimed. |
| Practitioner guidance | Clarification is available through the stable/conditional/unresolved and Pareto-first decision protocol; it is not a universally validated aggregation rule. |
| Conflicting retrieved evidence | Related-work coverage can be added, but scorer disagreement must not be conflated with contradictory source content; no completed contradiction experiment exists. |
| Code/data clarity | A canonical experiment and provenance map is available. Recovered outputs must not be described as submitted, and universal per-query completeness remains unsafe. |

## Public-safety controls

- The local confidential source is not under the repository root.
- Committed files contain precise paraphrases, IDs, ratings, confidence
  values, and response-control metadata only.
- No review timestamps, full summaries, full strengths/weaknesses, or
  verbatim question prose are stored.
- The exact-source filename is mentioned only as an untracked local input in
  the author’s instruction and is not copied into the repository.
- No raw modern-judge output, human-label rows, question/context/answer text,
  external-rater identity, or credential is added.

Final privacy and secret scan results are recorded in
`REVIEW_INGESTION_COMPLETE.md`.

## Unresolved items for Prompt 6

1. No completed modern-judge result exists; Version A must be complete without
   one.
2. Bibliographic metadata for the reviewer-nominated conflicting-source paper
   must be verified before the citation is inserted.
3. The full-paper revision venue/mechanism and any response character limit
   must be confirmed before paste-ready packaging.
4. Exact historical package/model revisions remain unlocked, so bitwise
   scorer regeneration cannot be promised.
5. Universal submitted per-query coverage, immutable preregistration timing,
   compensation, and IRB status remain prohibited claims.
6. Broader complex/agentic validation remains future work, not a rebuttal
   result.
7. A verified same-row human comparison of answer-only and
   context-conditioned NLI formats is not available.

## Prompt 6 readiness

`READY_FOR_PROMPT_6_WITH_QUARANTINED_EXCLUSIONS`

Reviewer-specific drafting is unblocked. Scientific and privacy exclusions
remain mandatory.
