# Fix 3 column documentation

`per_query.csv` extends Fix 2 rows with:

- `faith_deberta`: original DeBERTa-v3 NLI score.
- `faith_second_nli`: Vectara HEM or roberta-large-mnli score.
- `faith_ragas`: RAGAS-style LLM-as-judge faithfulness score.
- `ragas_reason`: short judge rationale.

`human_eval_template.jsonl` is an optional two-rater template. Fill
`rater_a_faithful` and `rater_b_faithful` with `0` or `1`, then rerun with
`--human_rated_path`.
