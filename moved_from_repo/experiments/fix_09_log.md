# Fix 9 Log - Self-Confidence Partial Correlations

**Status:** limited local run complete; full-control run pending better input.  
**Weakness addressed:** W9, CCS-confidence correlation might be mediated by
similarity or redundancy.

## Protocol

- Input: confidence-calibration per-query CSV.
- Outcome: model self-confidence.
- Predictor: CCS.
- Controls:
  - mean query-passage similarity;
  - passage redundancy, defined as mean pairwise passage similarity without
    the standard-deviation term.

## Command

```bash
python3 experiments/fix_09_partial_correlations.py \
  --input results/confidence_calibration/per_query.csv
```

If the full-control partial correlation does not survive, the paper demotes
the confidence result to "suggestive."

## Result

Files:

- `data/revision/fix_09/input_copy.csv`
- `results/revision/fix_09/partial_correlations.csv`
- `results/revision/fix_09/summary.md`

The available input, `results/confidence_calibration/per_query.csv`, does not
contain `mean_retrieval_similarity` or `passage_redundancy`, so the script
could only compute the no-control association:

| n | controls | partial Pearson r | partial Pearson p | partial Spearman rho | partial Spearman p | survives |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 60 | none | 0.360029 | 0.004720 | 0.481454 | 9.844e-05 | True |

Interpretation: because the actual controls are unavailable in the current
CSV, this does not fully resolve the confounding concern. Treat the confidence
result as suggestive unless a later confidence-calibration run includes the
required control columns.
