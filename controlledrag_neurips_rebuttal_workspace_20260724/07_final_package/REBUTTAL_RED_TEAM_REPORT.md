# Rebuttal Red-Team Report

## Status

Scientific/content status: `PASS_WITH_HUMAN_REVIEW_REQUIRED`

Privacy/secret status:
`PASS_FOR_PUBLIC_SAFE_SANITIZED_CONTENT_COMMIT_AND_PUSH`

## Attack surface

The red team reviewed the current/initial AC response, five reviewer
responses, shared fact surface, character counts, and final paste package
against the P0 gate, claim ledger, safe-number tables, experiment matrix,
metric dictionary, decision protocol, ingestion handoff, and repaired
modern-judge handoff.

## Findings

| Risk | Result | Evidence / mitigation |
| --- | --- | --- |
| Unsupported claims | Pass | The fact-check ledger contains 38 controls and distinguishes verified facts, method proposals, interpretations, and revision commitments. |
| Stale average-precision values | Pass | Only the locked `0.764813/0.928793/0.859367` triple appears in shared facts; no stale triple appears in paste text. |
| Matched `p=0.011` | Pass | It does not appear in paste-ready responses. |
| Human sample-size mixing | Pass | `n=99` and `n=100` are always described as separate; `wXNA` reports the two Spearman triples and the separate `n=100` average-precision endpoint without pooling. |
| Human protocol | Pass | Independent labeling before reconciliation is stated; no unconfirmed qualifications, compensation, IRB, LLM-assistance, or adjudicator identity is added. |
| Same-row human comparison | Pass | The `wXNA` response explicitly says answer-only versus context-conditioned NLI was not compared on the same human rows. |
| Scorer sign reversal | Pass | Always described as fixed-output/input-format sensitivity, never universal scorer correctness. |
| Scorer naming | Pass | Uses legacy answer-only zero-shot label proxy, RAGAS-style judge, and sklearn average precision. |
| Seven-axis overclaim | Pass | Always described as practical, non-unique, and non-exhaustive; the disclosure tier is separated from claim-critical stress testing and no factorial requirement is implied. |
| Broad generalization | Pass | Modern, complex, agentic, retriever, Qwen, cost, and long-form boundaries are explicit. |
| Re-encoding overstatement | Pass | Fixed-context re-encoding is not called fresh retrieval/generation. |
| Cost/Pareto overstatement | Pass | Guidance is point-estimate/Pareto-first and denies a universal winner. |
| Modern-judge contamination | Pass | Version A is complete; Version B is template-only; real rows remain zero. |
| Conflicting-evidence conflation | Pass | Cattan et al. is cited as contradictory-source work and separated from scorer disagreement; no experiment is claimed. |
| Artifact completeness | Pass | Responses explicitly avoid universal per-query completeness and label recovered rows. |
| Preregistration/IRB/compensation | Pass | No unsafe assertion appears. |
| Exact-review confidentiality | Pass | Responses contain sanitized paraphrases, not review transcripts; the full-workspace 10/12/15-word comparison found zero non-citation overlap. |
| AC temporal status | Pass | AC text is labeled current/initial, never final. |
| Unanswered questions | Pass | All 21 checklist items are covered by the AC or reviewer response files. |
| Character limits | Pass | Exact fields are AC 3,932; `uqxN` 1,819; `wXNA` 2,292; `diyB` 2,276; `d61o` 2,086; `wh9X` 2,082. All are below 10,000. |
| Response mechanics | Pass | Paste text has no links and treats manuscript changes as camera-ready commitments rather than claiming that a revised paper or supplement was uploaded during rebuttal. |
| Anonymity/deanonymization | Pass | Paste text includes no author identity, private contact information, or deanonymizing link. |
| AC acceptance rationale | Pass | The AC field states an evaluation-contribution case without venue lobbying or entitlement language. |
| Evidence hierarchy | Pass | Strong/medium/diagnostic/exploratory labels are consistent; axis inclusion is not equated with validation. |
| `wXNA` readability | Pass | Fixed-output contrasts precede slice-specific human numbers; AP and Spearman are not conflated; the missing same-row comparison is immediate and explicit. |
| `diyB` provenance candor | Pass | Three experiment groups and the canonical path are explicit; row-reconstructable/summary-verifiable wording does not hide missing universal reviewer-artifact coverage. |
| `d61o` agentic mapping | Pass | Every mapping is labeled procedural, and the falsifiability rule leaves unstable conclusions unresolved. |
| `wh9X` clarity | Pass | The field uses exactly four labeled sections and one numeric Figure 2 example while covering metrics, all seven categories, the citation, and revision order. |
| Discussion-bank isolation | Pass | No discussion-bank-only novelty or recovered-row answer leaked into paste text. |
| Paste synchronization | Pass | All six standalone bodies exactly match the corresponding package markers; the internal AC synthesis matches the AC field. |

## Adversarial interpretations rejected

- The input-format reversal cannot be rewritten as proof that
  context-conditioned NLI is correct.
- The 40-question long-form panel cannot be presented as complex-task
  validation.
- HotpotQA cost rows cannot be presented as a full multi-hop faithfulness
  experiment.
- The prepared modern-judge harness cannot be described as an executed
  evaluation.
- The human slices cannot be combined to increase apparent sample size.
- The Cattan et al. citation cannot be used to imply ControlledRAG ran a
  contradictory-context benchmark.
- Recovered fixed rows cannot be called part of the immutable submitted
  artifact.

## Remaining human checks

1. Approve the candid recovered-versus-submitted artifact wording.
2. Decide whether any response should be shortened for discussion dynamics.
3. Perform a final tone and priority pass.
4. Paste and visually inspect each OpenReview field.

## Final automated validation

- `git diff --check`: pass.
- CSV structural validation: 22/22 tables parse with consistent row widths.
- Markdown-table validation: 62/62 tables have consistent column widths.
- Stale-value and unsafe-language scan of paste bodies: zero matches.
- URL, raw-HTML, marker, internal-branch, and author-identity scan of paste
  bodies: zero matches.
- Confidential-source overlap: zero non-citation 10-, 12-, or 15-word
  windows; the public Cattan citation is the only overlap class.
- Secret scan: zero email, AWS, GitHub, OpenAI, Slack, private-key, or generic
  secret-assignment matches in changed files.

## Recommendation

The package is scientifically safe for professor review and safe to submit
after the tone, artifact-wording, paste-rendering, and final-author checks
above.
