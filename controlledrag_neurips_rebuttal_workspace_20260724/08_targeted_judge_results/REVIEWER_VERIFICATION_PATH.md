# Reviewer verification path

1. Read `public_tables/EXPERIMENT_ONE_GLANCE_MAP.md`.
2. Check the three main rows in `MODERN_JUDGE_MAIN_RESULTS.csv`.
3. Check observed interface differences and finite replicate counts in `MODERN_JUDGE_INTERFACE_DIFFERENCES.csv`.
4. Check strict validity, model revision, repair, and population counts in `MODERN_JUDGE_RESULT_RECEIPT.json`.
5. Read `CLAIM_INCLUSION_DECISION.md` for bounded and forbidden interpretations.
6. Run `python3 scripts/validate_release.py` in the source artifact.

This path takes a reviewer from claim to aggregate evidence, code, test, and receipt without exposing private rows.
