# Statistical correctness audit

- Paired contrasts operate within pair ID.
- Difference in contrasts uses the same 193 pair IDs.
- Human interface comparisons operate within row.
- The two human slices remain separate.
- Point estimates are observed full-sample statistics.
- Bootstrap is used only for percentile uncertainty.
- Seed is `20260724` for every primary calculation.
- Replicate count is 10,000.
- Non-finite Spearman replicates are filtered and counted.
- No invalid result is recoded.
- Average precision uses faithful `1` as positive.
- Brier scales score to `[0,1]`.

Result: `STATISTICAL_CORRECTNESS_PASS`.
