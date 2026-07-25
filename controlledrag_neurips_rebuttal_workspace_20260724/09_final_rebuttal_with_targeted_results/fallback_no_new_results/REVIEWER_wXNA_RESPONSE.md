# Response to Reviewer wXNA

## Paste-ready response

We agree with the distinction between measurement sensitivity and
measurement correctness. We also agree that the seven categories have uneven
empirical support and should not be presented as equally validated.

The evidence hierarchy is explicit. **Strong:** fixed-output scorer and
scorer-input analyses. **Medium:** human calibration and the matched-context
audit. **Diagnostic:** threshold, cost, retriever, and second-generator
probes. **Exploratory:** the long-form panel. Axis inclusion indicates
reporting importance, not equal empirical validation. The framework is
proposed to be procedurally portable across RAG settings; the numerical
effects observed here are not claimed to generalize beyond the tested cells.

Holding outputs and NLI backbones fixed, changing the scorer input reverses
the system comparison. On the 600-row panel, with 194 complete
baseline/HCPC-v1 pairs for each context-conditioned backbone, baseline minus
HCPC-v1 changes from `+0.017` to `-0.279` for DeBERTa and from `+0.044` to
`-0.081` for the second NLI backbone. This is fixed-output scorer-input
sensitivity, not fresh retrieval or generation.

The available human evidence gives calibration context without resolving the
requested interface comparison. On the separate `n=99` typical slice,
Spearman correlation for DeBERTa / the second NLI proxy / the RAGAS-style
judge is `0.103 / 0.394 / 0.549`; on the `n=100`
disagreement-targeted slice it is `-0.156 / 0.446 / 0.384`. On the `n=100`
binary task, average precision is `0.765 / 0.929 / 0.859`. These slices
answer different questions and are not pooled. These rows do not provide a
verified same-row human comparison between answer-only and
context-conditioned NLI.

We therefore revise the interpretation from “the context-conditioned call is
better” to “reasonable scorer interfaces can select different conclusions
and must be separately calibrated.” When baseline outperforms refinement
under an answer-only proxy but refinement outperforms baseline under
context-conditioned scoring, the correct report is not that either system
universally wins; the comparison is conditional on the scorer-input
convention.

The corrected conclusion is scorer sensitivity with slice-dependent
calibration—not universal correctness of any scorer interface.
