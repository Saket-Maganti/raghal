# Existing-Output Analysis Summary

## Scope

All analyses use fixed, provenance-safe outputs. No retrieval, generation,
model inference, external API, dataset download, or network access was used.
The executable script, input hashes, package versions, seeds, and output
tables are under `scripts/` and `results/`.

## Human verification

Both slices are structurally complete and remain separate. Pre-adjudication
agreement is 0.919 with kappa 0.774 on the `n=99` typical slice and 0.880 with
kappa 0.721 on the `n=100` disagreement-targeted slice. Their adjudicated
distributions are `79/16/4` and `74/26/0`, respectively.

Submitted scorer correlations, AUROC, and locked sklearn average precision
reproduce. The `n=99` primary endpoint remains ordinal; its determinate-only
binary calculation is a secondary sensitivity, not headline evidence.

## Scorer-ranking uncertainty

On the typical slice, RAGAS-style correlation exceeds the second proxy by
0.155 (95% paired bootstrap CI 0.017, 0.314). Both exceed the legacy DeBERTa
proxy. On the disagreement-targeted slice, second and RAGAS-style both exceed
legacy DeBERTa, but their direct ordering is unresolved: RAGAS minus second is
-0.062 (-0.234, 0.116).

Safe conclusion: the legacy DeBERTa proxy aligns weakly, while the ordering of
the two stronger scorers is slice-dependent. This does not establish a
universally best scorer.

## Answer-only versus context-conditioned scoring

For the paired fixed 600-row panel, the legacy answer-only proxies and
context-conditioned re-encodings produce materially different
baseline-minus-HCPC-v1 contrasts:

| Metric | Contrast | 95% paired bootstrap CI | Complete pairs |
| --- | ---: | ---: | ---: |
| Legacy DeBERTa proxy | 0.017 | (-0.004, 0.037) | 200 |
| Context-conditioned DeBERTa | -0.279 | (-0.338, -0.219) | 194 |
| Legacy second NLI proxy | 0.044 | (0.025, 0.063) | 200 |
| Context-conditioned second NLI | -0.081 | (-0.123, -0.042) | 194 |
| RAGAS-style judge | 0.130 | (0.076, 0.186) | 200 |

The context-minus-legacy difference of contrasts is -0.293
(-0.356, -0.230) for DeBERTa and -0.127 (-0.166, -0.089) for the second NLI.
This supports the narrow claim that the NLI calling convention matters. The
panel is fixed-context re-encoding, not fresh retrieval/generation, and the
context-conditioned implementation is not asserted to be universally
correct.

## Threshold transfer

Selected thresholds have mixed target behavior. Thresholds selected on
PubMedQA, Natural Questions, and TriviaQA are positive on four of five target
datasets; thresholds selected on SQuAD and HotpotQA are positive on three of
five. HotpotQA recovery is negative at every tested tau, while Natural
Questions recovery is positive at every tested tau. The result is a
conditional sensitivity finding, not evidence of universal threshold
transfer.

## Faithfulness, latency, and indexing

On HotpotQA, CRAG is the only point-estimate three-objective frontier system
and dominates HCPC-v2 and two-level RAPTOR on faithfulness, latency, and
indexing time. On SQuAD, all three systems lie on the three-objective frontier:
RAPTOR has the highest point-estimate faithfulness, CRAG has the lowest
latency/indexing burden, and HCPC-v2 occupies an intermediate trade-off.

With illustrative utility
`faithfulness - λ × (latency_seconds + indexing_seconds/query_volume)`, CRAG
wins every tested HotpotQA setting. The SQuAD winner changes among RAPTOR,
HCPC-v2, and CRAG as query volume and time penalty vary. These are bounded
deployment sensitivities over two datasets, not general cost claims.

## Coverage

The analyses cover 99 typical human rows, 100 targeted human rows, the fixed
7,500-row multimetric table, a 2,500-row matched-control panel, 600
context-rescored rows, 25 threshold cells, and 1,200 faithfulness/latency
rows. Coverage descriptions identify where submitted versus recovered
fixed-output provenance applies.

## Rebuttal-safe takeaways

1. The two-rater protocol and both separate human slices are complete and
   numerically reproducible.
2. The submitted sklearn average-precision convention is verified and stale
   historical values remain excluded.
3. Legacy answer-only NLI naming should be corrected; calling convention
   materially affects the fixed-subset conclusion.
4. Stronger scorer ranking, threshold transfer, and deployment utility are
   conditional on slice, dataset, and weighting choices.
