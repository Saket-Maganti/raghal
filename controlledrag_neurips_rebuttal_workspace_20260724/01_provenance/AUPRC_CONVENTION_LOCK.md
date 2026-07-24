# AUPRC Convention Lock

## Locked convention

For the submitted `n=100` disagreement-targeted human-evaluation slice:

- the positive class is `faithful`;
- `faithful` maps to 1 and `hallucinated` maps to 0;
- `unclear` maps to missing, although the adjudicated slice has zero unclear
  labels;
- the metric implementation is
  `sklearn.metrics.average_precision_score(y_true, score)`;
- scorer values are used as faithfulness scores, without sign reversal;
- the `n=100` slice is not pooled with the `n=99` typical slice.

## Recomputed submitted values

| Scorer | AUROC | Locked AUPRC |
| --- | ---: | ---: |
| Legacy DeBERTa proxy | 0.397609 | 0.764813 |
| Second NLI proxy | 0.793659 | 0.928793 |
| RAGAS-style judge | 0.717516 | **0.859367** |

The recomputation uses all 100 adjudicated rows from
`human_eval_final/n100_disagreement/annotation_batch_disagreement_100.csv`.
The input SHA-256 is
`83ac395bdce120c3b8def310e410191fb2969942d6796dd57dc48dd3dc5643b8`.

The submitted analysis script SHA-256 is
`142e40516fd165eae76f71a4feb10d655c5d50d13abbd7481c2a8112b1c48a16`.
The submitted AUROC/AUPRC table SHA-256 is
`4dcd47bc55d269928621bd5ff1f1a3f531334ee49259d11fc19ccb103d6fd982`.

## Superseded values

The historical `disagreement_alignment_n100.csv` reports AUPRC
`0.761753 / 0.928433 / 0.886240`. Its SHA-256 is
`fc205b6b792a53f013d7acd7bad3f57584967d32f0c325d4fbe693065919c9d2`.
Those values come from a superseded implementation and must not be used in
the rebuttal, supplement correction, table, figure, caption, or response
draft.

## Rebuttal-safe wording

> On the separately sampled `n=100` scorer-disagreement slice, submitted
> `sklearn` average precision was 0.765, 0.929, and 0.859 for the legacy
> DeBERTa proxy, second NLI proxy, and RAGAS-style judge, respectively.

This is a slice-specific alignment diagnostic, not a population estimate and
not evidence that one scorer is universally best.
