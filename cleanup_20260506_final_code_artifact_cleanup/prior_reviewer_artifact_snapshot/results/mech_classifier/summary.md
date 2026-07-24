# Mechanistic signal → coherent/fragmented classifier

- Rows: 20  (pairs: 10, features: 87)
- Task: predict `condition == 'fragmented'` from per-layer attention-entropy and retrieved-mass signals.

## Cross-validated performance

| model       |   auc_mean |   auc_std |   f1_mean |   acc_mean |
|:------------|-----------:|----------:|----------:|-----------:|
| logistic_l2 |      0.8   |    0.4    |    0.8    |       0.8  |
| logistic_l1 |      0.85  |    0.3    |    0.8    |       0.85 |
| gbdt        |      0.575 |    0.3841 |    0.4667 |       0.5  |

## Baseline

- Single-feature logistic on aggregate retrieved mass alone: AUC = 0.800
- Best multi-feature model: AUC = 0.850 (model = `logistic_l1`)

## Top-10 L1-logistic features

| feature                 |       coef |   abs_coef |
|:------------------------|-----------:|-----------:|
| mean_retrieved_mass_L13 | -0.826597  |  0.826597  |
| mean_retrieved_mass_L31 | -0.766391  |  0.766391  |
| mean_entropy_L2         |  0.483826  |  0.483826  |
| mean_entropy_L15        | -0.161775  |  0.161775  |
| mean_retrieved_mass_L10 | -0.100288  |  0.100288  |
| mean_retrieved_mass_L0  |  0.0890573 |  0.0890573 |
| mean_retrieved_mass_L27 |  0         |  0         |
| mean_entropy_L31        |  0         |  0         |
| mean_retrieved_mass_L6  |  0         |  0         |
| mean_retrieved_mass_L5  |  0         |  0         |

A mean AUC ≳ 0.80 supports the claim that the coherence paradox is reflected in internal-layer activations and not just in the output-layer NLI score. The top features indicate **where** in the forward pass the fragmentation signal is most visible.