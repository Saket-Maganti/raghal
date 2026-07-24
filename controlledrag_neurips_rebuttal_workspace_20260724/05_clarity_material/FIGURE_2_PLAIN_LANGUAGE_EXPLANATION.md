# Figure 2 Plain-Language Explanation

## One sentence

On the same fixed answers and with the same two NLI backbones, merely changing
the scorer call from answer-only label prediction to context-as-premise
entailment reverses the baseline-minus-aggressive-refinement contrast.

## One paragraph

Figure 2 changes the measurement call, not the RAG outputs: the 600 answers
and retrieved contexts were already fixed, and no new retrieval or generation
was run. The legacy calls classify the answer alone against candidate labels,
whereas the alternative calls pass retrieved context as the NLI premise and
the answer as hypothesis. For the 194 complete baseline/HCPC-v1 pairs, the
mean contrast changes from `+0.017` to `-0.279` for DeBERTa and from `+0.044`
to `-0.081` for the second NLI backbone, with 10,000-resample paired
bootstrap intervals. The figure therefore shows that scorer input format can
change even the direction of a system comparison; it does not establish that
context-conditioned NLI is universally correct.

## Caption-length version

Same fixed generations and NLI backbones, different scorer inputs: replacing
answer-only zero-shot label calls with context-as-premise NLI reverses the
baseline-minus-aggressive-refinement contrast on the balanced 600-row panel
(194 complete baseline/HCPC-v1 pairs; 10,000-resample paired bootstrap 95%
CIs). This is a calling-convention sensitivity, not fresh retrieval or
generation and not a claim that context-conditioned NLI is universally
correct.
