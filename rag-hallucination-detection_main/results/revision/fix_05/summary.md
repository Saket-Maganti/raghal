# Fix 5 - coherence-preserving noise

## Summary

| condition                    |   n_noise |   noise_rate |   n |    faith |   halluc |      sim |
|:-----------------------------|----------:|-------------:|----:|---------:|---------:|---------:|
| baseline                     |         0 |     0        | 200 | 0.680252 | 0.155    | 0.5358   |
| coherent_uninformative_noise |         1 |     0.333333 | 197 | 0.667338 | 0.126904 | 0.525405 |
| coherent_uninformative_noise |         2 |     0.666667 | 197 | 0.658515 | 0.152284 | 0.501794 |
| coherent_uninformative_noise |         3 |     1        | 197 | 0.638522 | 0.137056 | 0.450318 |
| hcpc_v1_refinement           |       nan |   nan        | 200 | 0.679045 | 0.11     | 0.5669   |
| random_noise                 |         1 |     0.333333 | 200 | 0.674134 | 0.125    | 0.402512 |
| random_noise                 |         2 |     0.666667 | 200 | 0.637596 | 0.145    | 0.254744 |
| random_noise                 |         3 |     1        | 200 | 0.628406 | 0.1      | 0.081838 |

## Slope Response

| condition                    |   faith_slope_per_noise_rate |   sim_slope_per_noise_rate |   drop_at_full_noise |
|:-----------------------------|-----------------------------:|---------------------------:|---------------------:|
| random_noise                 |                    -0.068592 |                  -0.481011 |             0.051845 |
| coherent_uninformative_noise |                    -0.043224 |                  -0.112631 |             0.041729 |
| hcpc_v1_refinement           |                   nan        |                 nan        |             0.001206 |
