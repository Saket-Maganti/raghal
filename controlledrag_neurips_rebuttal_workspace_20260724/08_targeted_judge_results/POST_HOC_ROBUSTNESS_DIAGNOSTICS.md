# Post-hoc robustness diagnostics

Every result here is a `post-hoc diagnostic`. None replaces the preregistered primary analysis.

| Diagnostic | Result |
| --- | --- |
| leave-one-pair-out range | 10.1563 to 11.4583 |
| maximum absolute single-pair influence | 0.8366 points |
| all leave-one-out estimates positive | yes |
| paired sign-flip test | two-sided Monte Carlo p = 0.000040, 200,000 draws |
| bootstrap seed sensitivity | all five predetermined seed intervals exclude zero |
| pair effects | 59 positive, 113 zero, 21 negative |
| worst-case 194-pair bound for invalid score | [10.3093, 10.8247] |

Predetermined diagnostic seeds were `20260724` through `20260728`. Their lower bounds range from 5.4922 to 5.6995 and upper bounds from 15.4922 to 15.5959.

Validity by system/interface ranges from 0.9921875 to 1.0. Maximum differential missingness is 0.0078125.

The accepted scores are discrete. Main-panel medians are 0 for both systems under answer-only, 50 for baseline and 0 for HCPC-v1 with context. The primary result is a paired mean estimand; these quantiles are descriptive.

No single pair determines the 10.62-point conclusion.
