# Response to Reviewer diyB

## Paste-ready response

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
