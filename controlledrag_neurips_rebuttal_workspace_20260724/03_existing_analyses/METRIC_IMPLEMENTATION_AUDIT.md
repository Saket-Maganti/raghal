# Metric Implementation Audit

## Status

`VERIFIED_WITH_NAMING_CORRECTION_AND_VERSION_LIMITATIONS`

The historical numerical outputs are internally reproducible, but the two
legacy NLI columns must be described as answer-only zero-shot label proxies,
not context-conditioned entailment scores.

## Rebuttal-relevant implementations

| Metric | Input and implementation | Aggregation / direction | Threshold and edge cases | Version evidence | Safe paper wording |
| --- | --- | --- | --- | --- | --- |
| Legacy DeBERTa proxy | Answer sentence is passed to a Transformers `zero-shot-classification` pipeline with candidate labels entailment/neutral/contradiction and `hypothesis_template="{}"`; retrieved context is not consumed by the call | mean entailment label probability across period-split answer segments; higher is more faithful; rounded to 4 decimals | `<0.5` is hallucinated; no segments returns 1.0; failed segments contribute 0.5 | model ID `cross-encoder/nli-deberta-v3-base`; `transformers>=4.40`, `torch>=2.3`; exact resolved package/model revision not recorded | “legacy DeBERTa zero-shot label proxy” |
| Legacy second NLI proxy | Default `roberta-large-mnli` uses the same answer-only zero-shot candidate-label call; the class also supports a Vectara HEM branch, but fixed outputs identify the proxy column | single answer-level entailment probability; higher is more faithful; rounded to 4 decimals | empty answer returns 1.0; `<0.5` is hallucinated; model-load fallback can change requested HEM to RoBERTa MNLI | model ID recorded; exact resolved package/model revision not recorded | “legacy second NLI proxy” |
| RAGAS-style judge | Custom local prompt passes question (1,000 chars), context (4,000), and answer (1,500) to the configured LLM; this is not the upstream `ragas` package | parsed scalar clamped to `[0,1]`; higher is more faithful | JSON preferred; fallback extracts first `0`/`1`-style number, else 0.0 | `langchain-ollama>=0.1`; judge backend/model stored with fixed rows; exact package/model revision not locked | “RAGAS-style judge,” never “official RAGAS implementation” |
| Context-conditioned NLI | Premise=context truncated to 2,048 characters; hypothesis=answer sentence; tokenizer pair truncated at 512 tokens; softmax entailment index resolved from model labels | mean per-sentence entailment probability; higher is more faithful | empty/failed rows become missing; 194 complete paired baseline/HCPC-v1 rows in the fixed 600-row panel | model IDs recorded; exact weights/revisions and generating runtime not locked | “fixed-context NLI re-encoding sensitivity” |
| Raw agreement | exact equality of the two pre-adjudication categorical labels | fraction equal; higher means more agreement | no adjudicated labels used | Prompt 03: NumPy 2.4.4 | “pre-adjudication raw agreement” |
| Cohen's kappa | `sklearn.metrics.cohen_kappa_score` on the two pre-adjudication categorical labels | unweighted nominal kappa; higher means more beyond-chance agreement | all categories retained, including `unclear` | Prompt 03: scikit-learn 1.8.0; requirements specify `>=1.4` | “unweighted pre-adjudication Cohen's kappa” |
| Pearson / Spearman / Kendall | scorer versus adjudicated numeric mapping, separately by slice | higher positive values mean closer alignment | requires nonconstant finite inputs; ordinal maps are documented in the crosswalk | Prompt 03: SciPy 1.17.1 | “slice-specific scorer-to-human alignment” |
| AUROC | `sklearn.metrics.roc_auc_score` | faithful/support class is positive; higher scorer value predicts positive | requires both classes | Prompt 03: scikit-learn 1.8.0 | report only with endpoint and slice |
| Average precision | `sklearn.metrics.average_precision_score` | faithful class is positive; higher scorer value predicts positive; non-interpolated sklearn AP | `n=100` locked; `n=99` only secondary determinate-row sensitivity | Prompt 03: scikit-learn 1.8.0 | “average precision,” with convention; avoid ambiguous “AUPRC” |
| Bootstrap CI | paired row resampling with replacement and percentile quantiles | 2.5th/97.5th percentiles | invalid single-class binary resamples omitted and counted | submitted seeds/resamples retained; Prompt 03 uses 10,000 resamples with recorded seeds | “95% paired percentile bootstrap CI” |
| Threshold recovery | fixed `recovery` column over dataset/tau cells | larger is better; values may fall below 0 or exceed 1 | descriptive grid, not a probability | fixed recovered output | “threshold-transfer sensitivity index” |
| Pareto status | maximize faithfulness while minimizing mean latency and one-time indexing time | nondominated within dataset | no statistical dominance test; point-estimate frontier only | fixed 1,200-row output | “point-estimate three-objective Pareto frontier” |
| Cost utility | `faithfulness - λ × (mean latency seconds + indexing seconds / query volume)` | higher utility is better | λ and query volume are illustrative sensitivity settings | Prompt 03 deterministic arithmetic | “illustrative cost-weight sensitivity” |

## Naming correction

The submitted `HallucinationDetector` docstring says the answer is checked
against retrieved context, and its `score_sentence` signature accepts a
premise. The actual pipeline call passes only the answer/hypothesis as the
sequence and never uses the premise. The second MNLI proxy behaves the same
way in its default branch. This is a semantic documentation discrepancy, not
a recomputation error.

## Package/version limits

The submitted requirements are lower bounds, not a lockfile. Exact
Transformers, PyTorch, LangChain, model-weight revisions, tokenizer revisions,
and the RAGAS-style judge model build are not recoverable from the fixed CSVs.
Prompt 03 therefore verifies existing values without claiming bitwise
regenerability of model scoring.
