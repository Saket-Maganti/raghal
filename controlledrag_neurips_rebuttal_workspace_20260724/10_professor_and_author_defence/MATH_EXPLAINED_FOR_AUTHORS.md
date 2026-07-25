# Math explained for authors

For each fixed pair, there are four scores: baseline and HCPC-v1 under answer-only and context-conditioned judging.

First calculate two within-pair effects:

```text
answer effect = baseline answer-only - HCPC-v1 answer-only
context effect = baseline with-context - HCPC-v1 with-context
```

Average each effect over the same 193 pairs:

```text
answer contrast = 3.316
context contrast = 13.938
```

Then:

```text
difference in contrasts = 13.938 - 3.316 = 10.622
```

The bootstrap resamples pair IDs and repeats the calculation. It gives uncertainty, not the displayed point estimate. The 95% interval is `[5.544, 15.492]`, so zero is outside.

For humans, AP asks whether higher scores rank faithful rows above non-faithful rows. Spearman asks whether score ranks move with the binary label. Boolean accuracy uses the judge's explicit true/false decision. Brier treats score/100 as a probability and measures squared error.

The 83-row and 72-row analyses resample rows separately. Constant-label or constant-score bootstrap samples can make a statistic undefined; those non-finite values are omitted from the CI distribution and counted.
