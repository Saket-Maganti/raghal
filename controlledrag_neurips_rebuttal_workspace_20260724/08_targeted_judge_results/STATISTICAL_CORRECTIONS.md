# Statistical corrections

The accepted package is scientifically usable, but its generated analysis tables require four presentation corrections.

1. **Direct point estimates.** Human interface differences must be the observed full-sample statistic, not the mean of bootstrap replicates.
2. **One seed.** The generated table used seed offsets for the context contrast and human analyses. Prompt B locks every final calculation to seed `20260724`.
3. **Diagnostic Spearman.** The generated point estimate was missing because some bootstrap samples produced non-finite correlations. The observed full-sample difference is `+0.2462864`. Only non-finite bootstrap statistics are discarded from the CI distribution.
4. **Common population.** All main estimates use the same 193 complete pairs.

These corrections change uncertainty endpoints slightly but do not change direction or inclusion.

The final public tables report:

- observed estimates;
- primary seed `20260724`;
- 10,000 resamples;
- finite-replicate counts;
- separate 83-row and 72-row slices.
