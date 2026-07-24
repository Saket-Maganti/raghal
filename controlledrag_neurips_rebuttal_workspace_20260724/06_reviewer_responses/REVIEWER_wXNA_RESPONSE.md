# Response to Reviewer wXNA

## Paste-ready response

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
