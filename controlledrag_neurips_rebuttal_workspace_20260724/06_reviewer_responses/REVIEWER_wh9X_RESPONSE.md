# Response to Reviewer wh9X

## Paste-ready response

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
