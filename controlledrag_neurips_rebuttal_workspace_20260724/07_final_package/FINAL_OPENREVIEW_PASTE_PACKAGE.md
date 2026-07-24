# Final OpenReview Paste Package

## Use instructions

- Treat the AC note as the current/initial meta-review, not the final
  meta-review.
- Paste each field separately.
- Use the text between the matching `PASTE_START` and `PASTE_END` markers;
  do not paste the markers.
- Version A is the complete recommended package. Do not insert the optional
  modern-judge template because no real run exists.
- Every field below is below the official 10,000-character per-review limit.
- Do not include links in any pasted response.

## Current/initial AC response

<!-- PASTE_START:meta_review -->
We appreciate the current AC assessment and agree that the paper’s main risk
is not the importance of the question, but whether a proposed standard is
accessible, empirically scoped, and operationally useful.

No revised paper can be uploaded during rebuttal, so we clarify the claim
boundary here and describe camera-ready changes if accepted. We separate two
claims. **Method:** ControlledRAG is a practical disclosure/audit procedure
with seven categories: generator; retrieval; context construction;
measurement/scorer; human calibration; threshold transfer; and cost. These
are a usable minimum for this audit, not a unique or exhaustive taxonomy;
authors disclose all seven but stress-test only claim-critical alternatives.
**Evidence:** the
numerical findings are bounded mainly to short-answer QA and 7B-class local
generators. The five-dataset threshold grid, two-dataset cost comparison,
retriever diagnostics, one Qwen2.5-7B probe, and exploratory 40-question
long-form panel are diagnostic, not broad validation of complex, agentic, or
modern-judge RAG.

We explicitly grade evidence strength. The fixed-output scorer and input
format analyses are strongest; human and matched-context evidence is
medium-strength; generator, retriever, cost, and long-form cells are bounded
or exploratory. No modern-judge result is claimed: the optional package
remains repaired, prepared, and unexecuted, with zero real rows scored.

If accepted, the camera-ready abstract, introduction, setup, and experiment
organization will be substantially rewritten. Each metric will state its
input, output, direction, aggregation, threshold, and slice. The historical
NLI scores are legacy
answer-only zero-shot label proxies; the custom third scorer is RAGAS-style,
not official RAGAS. Figure 2 holds outputs and backbones fixed and changes only
the scorer input. On 194 complete pairs, the mean contrast changes from
`+0.017` to `-0.279` for DeBERTa and from `+0.044` to `-0.081` for the second
backbone. This demonstrates input-format sensitivity, not that
context-conditioned NLI is universally correct.

Our practitioner protocol is to define the deployment endpoint and
constraints; disclose all seven categories; calibrate on a relevant human
slice; stress-test choices that can change sign, rank, threshold, or deployment
choice; then classify the result as stable, conditional, or unresolved. For
cost-sensitive decisions, apply explicit constraints or weights only after a
Pareto screen. No universal scorer or aggregation rule is claimed.

To address experiment and code clarity, our map lists every cell’s
dataset/split, `n`, generator, retriever/context, scorer input, seed status,
output origin, uncertainty, evidence grade, and canonical source. Recovered
fixed rows will not be described as submitted, and we will not claim complete
per-query coverage.

We also cite Cattan et al., “DRAGged into Conflicts: Detecting and
Addressing Conflicting Sources in Search-Augmented LLMs,” arXiv:2506.08500
(2025). Contradictory retrieved evidence is distinct from scorer disagreement,
and we do not claim a completed contradictory-context experiment.
<!-- PASTE_END:meta_review -->

## Reviewer `uqxN`

<!-- PASTE_START:uqxN -->
Thank you for recognizing the value of the audit, reusable artifacts, scorer
input-format result, and explicit cost dimension. We agree that the three
questions you raise define the framework’s practical boundary.

**Modern judges and reward models.** We have not established that the observed
numerical effects transfer to current LLM judges or task-specific reward
models, and we state this directly. The protocol is scorer-agnostic in
the limited procedural sense that any scorer must disclose its identity,
version, inputs, scale, aggregation, threshold, and human calibration. That
does not make our existing experiments a validation of untested judge
families.

**Seven axes and overhead.** We clarify that seven is a practical minimum
for this audit, not a unique or exhaustive taxonomy. Authors should disclose
all seven entries, using “not varied” or “not measured” when appropriate, but
need not run a full factorial grid. Stress testing is required only for a
reasonable alternative that could change the claim’s sign, ranking, threshold
decision, or deployment choice. This preserves diagnostic value while keeping
the burden proportional to the claim.

**Conflicting outcomes and deployment choice.** Our operational rule is to
define the deployment endpoint and constraints first; calibrate scorers
on a relevant human slice; vary claim-critical choices; then classify the
result as stable, conditional, or unresolved. For cost-sensitive selection,
remove point-estimate-dominated systems before applying explicit latency,
indexing, or query-volume constraints. If plausible settings select different
systems, report the conditional Pareto set rather than manufacture one global
winner. Our two-dataset cost audit illustrates this procedure but is not a
universal economic ranking.
<!-- PASTE_END:uqxN -->

## Reviewer `wXNA`

<!-- PASTE_START:wXNA -->
Thank you for the careful distinction between measurement sensitivity and
measurement correctness. We agree with that distinction and with your
assessment that the seven axes have uneven empirical support.

We grade the evidence explicitly. The fixed-output scorer comparison and
input-format reversal are the strongest audited cells; the two separate human
slices and matched-context audit are medium-strength diagnostics; the
retriever, second-generator, cost, and long-form cells are bounded or
exploratory. “Included as an axis” is not “equally validated.”

We therefore narrow the empirical claim. The main evidence is concentrated in
short-answer QA and 7B-class local models. The five-dataset threshold grid,
two-dataset cost audit, bounded retriever checks, one Qwen2.5-7B probe, and
40-question MS-MARCO/QASPER panel add diagnostic breadth, but none establishes
broad generalization.

Figure 2 holds the 600 answers and contexts fixed and changes only the scorer
call. For 194 complete baseline/HCPC-v1 pairs, the mean contrast changes from
`+0.017` to `-0.279` for DeBERTa and from `+0.044` to `-0.081` for the second
NLI backbone when moving from answer-only label prediction to
context-as-premise NLI. This supports the narrower conclusion that scorer
input format can reverse a system comparison. It does not establish that
context-conditioned NLI is universally correct.

Our human evidence is also narrower than the comparison you request. The
separate `n=99` typical and `n=100` disagreement-targeted slices compare the
two legacy answer-only proxies and a custom RAGAS-style judge with adjudicated
labels; they do not provide a verified same-row human comparison of
answer-only versus context-conditioned NLI. We do not imply otherwise. When
scorers or human slices disagree, our guidance classifies the
conclusion as conditional or unresolved rather than select a universal scorer.
<!-- PASTE_END:wXNA -->

## Reviewer `diyB`

<!-- PASTE_START:diyB -->
Thank you for highlighting that the empirical contribution and artifact path
were difficult to reconstruct. We agree that the paper needs one explicit
experiment map and a clearer dataset description.

The work is not only a position statement, although its empirical scope is
bounded. The verified inventory includes: (i) a SQuAD matched-context audit
with 200 HIGH/LOW pairs; (ii) a fixed 7,500-row SQuAD scorer comparison with
2,500 rows per condition and generation seeds 41–45; (iii) a balanced
600-row fixed-output scorer-input analysis; (iv) separate `n=99` typical and
`n=100` disagreement-targeted human-calibration slices; (v) a 5×5 threshold
grid over PubMedQA, Natural Questions, SQuAD, TriviaQA, and HotpotQA; and
(vi) a cost comparison on SQuAD and HotpotQA with three systems × 200 rows per
dataset. Bounded diagnostics additionally include a 720-row
SQuAD/PubMedQA retriever pilot, a separate 1,200-row fixed-context
re-encoding panel, one 300-row Qwen2.5-7B probe, and an exploratory
40-question MS-MARCO/QASPER panel.

For clarity, our experiment map identifies each cell by dataset/split, sample
size, generator, retriever/context, scorer input, available seed, output
origin, uncertainty method, evidence grade, and canonical source. It also
separates the two legacy answer-only zero-shot label proxies from the custom
question+context+answer RAGAS-style judge and from fixed-output
context-conditioned NLI. If accepted, we will add this table to the
camera-ready.

We clarify artifact navigation rather than claim completeness. Some
fixed rows used for verification were recovered during the audit rather than
present in the immutable reviewer artifact, and exact historical
model/package revisions are not locked. The camera-ready, if accepted, will
label outputs as generated, rescored, re-encoded, imported, or aggregated and
will not claim that every audited cell shipped a complete per-query file.
This experiment map and provenance boundary make the empirical contribution
assessable without overstating reproducibility.
<!-- PASTE_END:diyB -->

## Reviewer `d61o`

<!-- PASTE_START:d61o -->
Thank you for recognizing the importance of standardized RAG-faithfulness
reporting and for identifying generalizability as the central limitation. We
agree that the current experiments do not validate the observed numerical
effects in complex or agentic RAG.

We distinguish the methodological and empirical claims. The methodological
proposal is a disclosure procedure: report the generation setup, retrieval
setup, context construction, measurement rule, calibration evidence,
threshold portability, and deployment cost; identify claim-critical
alternatives; and classify the result as stable, conditional, or unresolved.
This procedure can be
instantiated for multi-hop, long-form, or agentic systems, but that
applicability claim is procedural. It does not imply that our measured effect
sizes or rankings transfer to those settings.

The numerical evidence remains bounded primarily to short-answer QA and
7B-class local generators. The available breadth is:
a five-dataset threshold grid, a HotpotQA/SQuAD cost cell, bounded retriever
diagnostics, one Qwen2.5-7B probe, and an exploratory 40-question
MS-MARCO/QASPER long-form panel. The long-form panel is too small for a broad
claim, and the HotpotQA cost cell is not a full multi-hop faithfulness
validation.

For complex applications, the concrete guidance is to define the task-level
decision and endpoint first, disclose all seven categories, calibrate on a
deployment-relevant human slice, and stress-test only choices capable of
changing the sign, rank, threshold, or deployment decision. A result that
depends on those choices should be reported conditionally rather than
aggregated into a single universal score. Broader complex-task validation
remains future work.
<!-- PASTE_END:d61o -->

## Reviewer `wh9X`

<!-- PASTE_START:wh9X -->
Thank you for identifying where compression made the paper inaccessible. We
agree that a proposed reporting standard must explain its metrics, figure,
and checklist criterion more directly. A revised paper cannot be uploaded
during rebuttal, so we clarify the issues here; if accepted, we will
substantially reorganize the abstract, introduction, setup, and experiment
map in the camera-ready.

**Metrics.** The historical DeBERTa score is an answer-sentence-only
zero-shot probability for the label “entailment”; the second historical NLI
score is a whole-answer-only zero-shot label probability. Neither consumes
retrieved context in its legacy call. The third score is a custom
question+context+answer RAGAS-style judge, not the official `ragas` package.
For binary human comparison we use sklearn average precision with
`faithful=1`, higher scores indicating faithfulness. If accepted, the
camera-ready will state each metric’s input, output, direction, aggregation,
threshold, and human slice beside the result.

**Figure 2.** The answers, contexts, and two NLI backbones are fixed; only the
scorer input changes. For 194 complete baseline/HCPC-v1 pairs, the mean
baseline-minus-HCPC-v1 contrast changes from `+0.017` to `-0.279` for
DeBERTa and from `+0.044` to `-0.081` for the second backbone when moving
from answer-only label prediction to context-as-premise NLI. The figure shows
input-format sensitivity, not fresh retrieval/generation and not that
context-conditioned NLI is universally correct.

**Why these seven entries.** The inclusion rule is operational: include a
category when leaving it implicit lets a reader substitute another reasonable
choice and change the claim or deployment decision. Generator changes the
answer process; retriever changes the evidence surface; context structure
changes the presented evidence; scorer changes measurement; human
calibration anchors interpretation; threshold transfer governs operational
classification; and cost governs deployment choice. These are practical,
non-redundant disclosure categories for this audit, not a unique or exhaustive
taxonomy.

**Conflicting sources.** We add Arie Cattan et al., “DRAGged into
Conflicts: Detecting and Addressing Conflicting Sources in Search-Augmented
LLMs,” arXiv:2506.08500 (2025). That work concerns contradictory information
among retrieved sources; our result concerns disagreement among scorers on
fixed outputs. We distinguish them explicitly and do not claim that we
completed a contradictory-context experiment. If accepted, this distinction
and citation will be added to the camera-ready.
<!-- PASTE_END:wh9X -->

## Optional modern-judge insertion

Do not paste this section now. The optional package remains
`PROMPT_05_REPAIRED_PREPARED_NOT_EXECUTED`; real rows scored: zero. The
Version B template is retained only in
`06_reviewer_responses/SHARED_FACTS_AND_NUMBERS.md` and
`06_reviewer_responses/REVIEWER_uqxN_RESPONSE.md`.
