# Fix 3 Human Evaluation Instructions

## Goal

Judge whether each generated answer is supported by the retrieved context. Use only the provided passages, not outside knowledge.

## Files

- `human_eval_rater_a.csv`: annotation sheet for rater A.
- `human_eval_rater_b.csv`: annotation sheet for rater B.
- `human_eval_adjudication_template.csv`: template for resolving disagreements after both raters finish.

Do not edit `id`, `dataset`, `condition`, `question`, `answer`, or passage columns.

## Labels

Use exactly one of these labels in the `label` column:

- `supported`: all substantive claims in the answer are supported by the retrieved context.
- `partially_supported`: the answer is partly supported, but omits an important qualifier, overstates the evidence, or adds unsupported details.
- `unsupported`: the answer is absent from the context, contradicted by the context, or not justified by the context.

## Rating Rules

- Judge answer support by the retrieved passages only.
- Do not reward an answer because it is true from memory or web knowledge.
- If the context supports the main answer but the answer adds unsupported side details, use `partially_supported`.
- If the context contradicts the answer, use `unsupported`.
- If the answer says the information is unavailable, mark it `supported` only when the provided context really does not contain the answer.
- Use `notes` for uncertainty, contradictions, or cases that need adjudication.

## After Annotation

1. Rater A fills only `label` and `notes` in `human_eval_rater_a.csv`.
2. Rater B fills only `label` and `notes` in `human_eval_rater_b.csv`.
3. Merge labels into `human_eval_adjudication_template.csv`.
4. Resolve disagreements in `adjudicated_label`.
5. Report Cohen's kappa on rater labels and Spearman correlations between adjudicated labels and each automatic metric.
