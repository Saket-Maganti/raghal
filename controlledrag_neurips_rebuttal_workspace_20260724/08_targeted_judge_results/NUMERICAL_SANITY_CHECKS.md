# Numerical sanity checks

1. `37.357513 - 23.419689 = 13.937824`.
2. `8.756477 - 5.440415 = 3.316062`.
3. `13.937824 - 3.316062 = 10.621762`.
4. All main CI endpoints are ordered.
5. The difference-in-contrasts CI excludes zero.
6. Every AP lies in `[0,1]`.
7. Every Boolean metric lies in `[0,1]`.
8. Confusion-matrix cells sum to 83 and 72.
9. Typical differences equal `0.981699-0.962788` and `0.250745-0.117791`.
10. Diagnostic differences equal `0.864252-0.798559` and `0.299195-0.052908`.
11. Valid plus invalid equals 1,510.
12. Differential missingness is below 0.02.

All checks pass.
