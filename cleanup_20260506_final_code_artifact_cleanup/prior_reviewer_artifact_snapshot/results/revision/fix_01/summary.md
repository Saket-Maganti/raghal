# Fix 1 - causal coherence intervention

This experiment tests whether HIGH-CCS contexts produce more faithful
answers than LOW-CCS contexts when mean per-passage query similarity is
matched within +/-0.02.

## Match diagnostics

| dataset   |   n_pairs_constructed |   mean_sim_high |   mean_sim_low |   mean_abs_sim_gap |   max_abs_sim_gap |   mean_ccs_high |   mean_ccs_low |   mean_ccs_gap |   min_ccs_gap |   mean_overlap |   max_overlap |   mean_bucket_size |
|:----------|----------------------:|----------------:|---------------:|-------------------:|------------------:|----------------:|---------------:|---------------:|--------------:|---------------:|--------------:|-------------------:|
| squad     |                   200 |        0.423588 |       0.421478 |           0.006351 |          0.018512 |         0.67006 |       0.137426 |       0.532634 |      0.264139 |          0.395 |             1 |             255.44 |

## Paired faithfulness test

| dataset   |   n_pairs |   mean_faith_high |   mean_faith_low |   mean_diff_high_minus_low |   wilcoxon_stat |   wilcoxon_p_greater |   cohens_dz |   boot_ci95_lo |   boot_ci95_hi |   hallucination_rate_high |   hallucination_rate_low |   matched_odds_ratio_low_vs_high |   discordant_low_only |   discordant_high_only |   mean_similarity_delta_high_minus_low |   max_abs_similarity_delta |   similarity_wilcoxon_stat |   similarity_wilcoxon_p_two_sided | h1_supported   |
|:----------|----------:|------------------:|-----------------:|---------------------------:|----------------:|---------------------:|------------:|---------------:|---------------:|--------------------------:|-------------------------:|---------------------------------:|----------------------:|-----------------------:|---------------------------------------:|---------------------------:|---------------------------:|----------------------------------:|:---------------|
| squad     |       200 |          0.636195 |         0.638587 |                  -0.002392 |          8638.5 |             0.628268 |   -0.017086 |      -0.021651 |       0.016819 |                     0.165 |                     0.09 |                         0.387755 |                     9 |                     24 |                                0.00211 |                   0.018512 |                       7067 |                       0.000272884 | False          |

Decision rule: H1 is supported only when the one-sided paired Wilcoxon
p-value is < 0.05, Cohen's dz is > 0.2, the 10000-resample bootstrap
CI on the mean paired difference excludes 0, and the max similarity
gap remains <= 0.02 by construction.

If this rule fails, the paper must downgrade causal/mechanistic wording.
