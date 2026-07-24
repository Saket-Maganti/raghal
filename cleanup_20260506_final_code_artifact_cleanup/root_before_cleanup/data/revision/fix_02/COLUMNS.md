# Fix 2 column documentation

## `per_query.csv`

One row per `(dataset, seed, query, condition)`. Important columns:

- `faithfulness_score`: DeBERTa-v3 NLI entailment score.
- `is_hallucination`: `faithfulness_score < 0.5`.
- `mean_retrieval_similarity`: query-to-context retrieval similarity.
- `refined`: whether HCPC/HCPC-v2 changed the context.
- `context`: generated-context text, retained for Fix 3 multi-metric scoring.

## `headline_table.csv`

Aggregated pooled rows with bootstrap 95% CIs for continuous metrics and
Wilson score CIs for hallucination rate.
