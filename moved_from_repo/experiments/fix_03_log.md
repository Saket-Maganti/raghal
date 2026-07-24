# Fix 3 Log - Multi-Metric Faithfulness

**Status:** complete for automated metrics; optional human annotation pending.  
**Weakness addressed:** W3, reliance on a single DeBERTa NLI scorer.

## Protocol

- Input: `data/revision/fix_02/per_query.csv`.
- Metrics:
  - Existing DeBERTa-v3 NLI score.
  - Second NLI model: `vectara/hallucination_evaluation_model` by default,
    with `roberta-large-mnli` as a supported fallback.
  - RAGAS-style LLM-as-judge faithfulness via `src/ragas_scorer.py`.
- Primary sample: the upgraded Fix 2 headline cell.
- Optional human eval: stratified `n=100`, two annotators, Cohen's kappa.

## Statistics

- Pairwise Pearson and Spearman correlations between the three automated
  faithfulness measures.
- If human labels are provided: Cohen's kappa and Spearman agreement with
  each automated metric.

## Command

```bash
python3 experiments/fix_03_multimetric_faithfulness.py \
  --input data/revision/fix_02/per_query.csv \
  --second_nli_model roberta-large-mnli \
  --judge_backend ollama \
  --judge_model mistral \
  --build_human_eval \
  --human_n 100
```

Zero-dollar stronger run: keep the local judge, and prioritize the second NLI
plus manual `n=100` two-annotator evaluation. Paid/API judges are intentionally
not part of the no-spend path.

```bash
python3 experiments/fix_03_multimetric_faithfulness.py \
  --input data/revision/fix_02/per_query.csv \
  --second_nli_model vectara/hallucination_evaluation_model \
  --judge_backend ollama \
  --judge_model mistral \
  --build_human_eval \
  --human_n 100
```

## Output

- `data/revision/fix_03/per_query.csv`
- `data/revision/fix_03/human_eval_template.jsonl`
- `results/revision/fix_03/table1_multimetric.csv`
- `results/revision/fix_03/metric_correlations.csv`
- `results/revision/fix_03/human_eval_agreement.csv` after annotation

## Result

Source package:

- `Downloads/fix3_4_t4x2_outputs.zip`

Verified output:

- Total rows: `7500`.
- Missing metric scores: `0`.
- Scorer error rows: `0`.
- Human-eval template size: `99`.

Condition means:

| condition | n | DeBERTa | second NLI | RAGAS |
| --- | ---: | ---: | ---: | ---: |
| baseline | 2500 | 0.660947 | 0.350109 | 0.729640 |
| hcpc_v1 | 2500 | 0.650271 | 0.318418 | 0.590434 |
| hcpc_v2 | 2500 | 0.661196 | 0.350878 | 0.727948 |

Metric correlations:

| metric pair | Pearson r | Spearman rho |
| --- | ---: | ---: |
| DeBERTa vs second NLI | 0.258666 | 0.265295 |
| DeBERTa vs RAGAS | 0.181871 | 0.212055 |
| second NLI vs RAGAS | 0.674177 | 0.651497 |

Interpretation: DeBERTa has weak agreement with the alternate metrics, while
second NLI and RAGAS agree more strongly. HCPC-v2 is close to baseline across
all automated metrics; HCPC-v1 drops most sharply under RAGAS.
