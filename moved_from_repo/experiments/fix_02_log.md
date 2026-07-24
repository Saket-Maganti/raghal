# Fix 2 Log - Headline-Cell Rigor Upgrade

**Status:** complete; result generated and locally available.  
**Weakness addressed:** W2, the original headline cell used only `n=30`.

## Hypothesis

The SQuAD/Mistral refinement paradox and HCPC-v2 recovery remain visible when
the headline cell is scaled to `n=500` queries and five seeds.

## Protocol

- Dataset: SQuAD validation.
- Generator: Mistral-7B via Ollama unless `--backend` overrides it.
- Conditions: baseline, HCPC-v1, HCPC-v2.
- Query sample: `n=500` per seed, seeds `41 42 43 44 45`.
- Retrieval corpus: first `600` SQuAD validation contexts.
- Frozen thresholds: HCPC-v1 `(sim=0.50, ce=0.00)`, HCPC-v2
  `(sim=0.45, ce=-0.20)`.
- No tau retuning.

## Statistics

- Bootstrap 95% CIs with `10000` resamples for faithfulness, retrieval
  similarity, and refine rate.
- Wilson score 95% CI for hallucination rate.
- Paired Wilcoxon and Cohen's `d_z` for same-query faithfulness contrasts.

## Command

```bash
python3 experiments/fix_02_scaled_headline_n500.py \
  --datasets squad \
  --n 500 \
  --seeds 41 42 43 44 45 \
  --backend ollama \
  --model mistral \
  --max_contexts 600
```

## Output

- `data/revision/fix_02/per_query.csv`
- `data/revision/fix_02/COLUMNS.md`
- `results/revision/fix_02/headline_table.csv`
- `results/revision/fix_02/paired_contrasts.csv`
- `results/revision/fix_02/summary.md`

## Result

- Total rows: `7500`.
- Baseline mean faithfulness: `0.660947`.
- HCPC-v1 mean faithfulness: `0.650271`.
- HCPC-v2 mean faithfulness: `0.661196`.
- HCPC-v2 refine rate: `0.7048`.
- Interpretation: HCPC-v1 is below baseline in the scaled headline run, while
  HCPC-v2 recovers most of that loss and remains close to baseline. The old
  `n=30` headline cell should be described as a pilot.

## Honest Interpretation Template

If CIs are wide or HCPC-v2 recovery is smaller than the old n=30 estimate,
the old headline wording must be replaced by the scaled estimate. The n=30
cell should be described as a pilot only.
