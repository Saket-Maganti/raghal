# Review Ingestion Handoff

## Handoff status

`READY_FOR_PROMPT_6_WITH_QUARANTINED_EXCLUSIONS`

The exact-review blocker from prior handoffs is resolved. Use the sanitized
maps rather than the confidential local export for all drafting work:

- `01_provenance/REVIEWER_CONCERN_MATRIX.md`;
- `01_provenance/META_REVIEW_RESPONSE_MAP.md`;
- `06_reviewer_responses/DIRECT_QUESTION_CHECKLIST.md`; and
- `06_reviewer_responses/EXACT_REVIEW_INGESTION_REPORT.md`.

No final rebuttal has been drafted.

## Reviewer order and movement targets

| Order | Target | Why now | Realistic target |
| ---: | --- | --- | --- |
| 1 | AC `Ji7w` | Controls the synthesis and explicitly elevates clarity, scope, uneven support, guidance, and three negative reviews. | Move the assessment from “not ready” toward borderline/revision-remediable. |
| 2 | `d61o` (3/4) | High-confidence borderline reviewer; scope and applicability can be answered with honest claim narrowing and a concrete protocol. | 3→4 |
| 3 | `diyB` (2/3) | AC requests explicit code/data/experiment clarification; empirical inventory corrects an incomplete position-paper reading. | 2→3 |
| 4 | `wh9X` (1/3) | AC adopts the metric, checklist, clarity, and citation concerns. | 1→2; 1→3 only if revision commitments are accepted |
| 5 | `wXNA` (4/1) | Already positive with low confidence; evidence grading and sign-flip caution can consolidate or improve the score. | Preserve 4; plausible 4→5 |
| 6 | `uqxN` (5/4) | Protect the accept by answering operational/generalization questions without overclaiming. | Preserve 5 |

## Recommended Prompt 6 structure

1. AC synthesis: concede bounded scope and uneven support, then separate the
   portable audit procedure from non-portable numerical findings.
2. Metrics/Figure 2/checklist clarity: use the locked dictionary, plain
   figure explanation, and seven-axis rationale.
3. Empirical/code/data inventory: give dataset, `n`, generator, retriever,
   scorer input, seed status, output origin, uncertainty, and evidence grade.
4. Practitioner guidance: stable/conditional/unresolved classification,
   deployment-relevant calibration, claim-critical stress testing, then a
   Pareto-first cost decision.
5. Reviewer-specific replies: answer every item in the direct-question
   checklist and mark it complete only after fact checking.
6. Related work: verify and add the nominated conflicting-source citation,
   while stating that contradictory retrieved content differs from metric
   disagreement.

## Evidence anchors

- Scope and evidence strength:
  `05_clarity_material/EXPERIMENT_EVIDENCE_MATRIX.md` and
  `SCOPE_AND_GENERALIZATION_STATEMENT.md`.
- Metrics and naming: `05_clarity_material/METRIC_DICTIONARY.md`.
- Human values: `02_human_eval/HUMAN_EVAL_SAFE_NUMBERS.csv`.
- Fixed-output uncertainty and sign reversal:
  `03_existing_analyses/NEW_REBUTTAL_SAFE_NUMBERS.csv`.
- Practitioner action: `05_clarity_material/CONTROLLEDRAG_DECISION_PROTOCOL.md`.
- Claim-by-claim source and ceiling:
  `01_provenance/CLAIM_TO_EVIDENCE_LEDGER.csv`.
- Automatic failure conditions: `01_provenance/P0_INTEGRITY_GATE.md`.

## What not to claim

These constraints consolidate the prior handoffs and are mandatory until
Prompt 6 creates its final `WHAT_NOT_TO_CLAIM.md`:

1. Do not use stale average-precision values. The separate `n=100` sklearn AP
   values are `0.764813 / 0.928793 / 0.859367`.
2. Do not use the unreproduced matched binary `p=0.011`. If needed, the only
   safe replacement is exact two-sided `p=0.013531` with the convention
   stated; omitting the p-value is safer.
3. Do not pool the `n=99` typical and `n=100` disagreement-targeted human
   slices or imply either is population prevalence.
4. Do not call the legacy NLI columns context-conditioned entailment. They
   are legacy answer-only zero-shot label proxies.
5. Do not call the custom scorer official RAGAS; use “RAGAS-style judge.”
6. Do not call context-conditioned NLI universally correct or ground truth.
7. Do not call fixed-context rescoring/re-encoding fresh retrieval or
   generation.
8. Do not call the seven axes mathematically unique, formally exhaustive, or
   equally validated.
9. Do not broaden the Qwen, retriever, long-form, threshold, cost, or
   multi-retriever probes into universal evidence.
10. Do not call point-estimate Pareto membership statistical dominance or
    claim a universal cost winner.
11. Do not claim threshold transfer is universal.
12. Do not claim a modern-judge result. The package is prepared but
    unexecuted; real rows scored: zero.
13. Do not claim complete submitted per-query coverage; some verified fixed
    rows were recovered and must be labeled as such.
14. Do not assert immutable preregistration timing, compensation, IRB status,
    exact external-rater identity, or exact historical package/model
    revisions.
15. Do not conflate contradictory retrieved evidence with disagreement among
    scorers.
16. Do not claim that a full manuscript rewrite has already been completed.

## Remaining unresolved questions

- What OpenReview character limit and response structure apply?
- Can the manuscript itself be revised during this response phase, or should
  all rewrite commitments be future-facing?
- What is the verified bibliographic record for the conflicting-source paper
  nominated by `wh9X`?
- Will the authors run the optional modern judge later? Prompt 6 must remain
  complete if the answer is no.
- Which exact artifact path should be named in the final response without
  implying universal per-query completeness?

## Prompt 6 gate

Prompt 6 is ready to start if it:

- treats every row in `DIRECT_QUESTION_CHECKLIST.md` as mandatory;
- uses only verified ledger claims within their safety language;
- keeps Version A complete without a modern-judge result;
- preserves all privacy constraints; and
- does not treat score-movement targets as promises.
