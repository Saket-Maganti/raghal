# Equation-to-code traceability

| Mathematical object | Private independent implementation | Public canonical implementation | Test |
| --- | --- | --- | --- |
| paired system contrast | `recompute_prompt_b.py: paired score difference` | source artifact `src/controlledrag/metrics.py:paired_contrast` | source artifact tests 01-04 |
| difference in contrasts | private common-pair array | source artifact `difference_in_contrasts` | tests 03 and 05 |
| percentile paired bootstrap | private `bootstrap_mean` | source artifact `percentile_mean_ci` | tests 06-10 |
| strict parser | private byte-equivalent rule | source artifact `strict_parse_judge_output` | tests 11-15 |
| locked counts and population | private invariant assertions | public result receipt | tests 16-19 |

The private script is untracked because it reads private rows. The public implementation uses only toy inputs and aggregate contracts.
