# Fix 4 Log - Cross-Dataset Hyperparameter Generalization

**Status:** complete; result generated and locally available.  
**Weakness addressed:** W4, possible tau-tuning leakage.

## Protocol

- Datasets: SQuAD, PubMedQA, HotpotQA, Natural Questions, TriviaQA.
- Tune threshold tau on each dataset and evaluate that frozen tau on every
  other dataset.
- Default grid: `0.30 0.40 0.50 0.60 0.70`.
- Sample: `n=100` per dataset/tau.
- Generator: Mistral-7B unless backend override is supplied.

## Recovery Definition

`recovery = (faith_ccs_gate - faith_hcpc_v1) / (faith_baseline - faith_hcpc_v1)`

## Flag Rule

If diagonal recovery exceeds mean off-diagonal recovery by more than `0.03`,
the gap must be flagged honestly in the discussion/limitations section.

## Command

```bash
python3 experiments/fix_04_tau_generalization.py \
  --datasets squad pubmedqa hotpotqa naturalqs triviaqa \
  --taus 0.30 0.40 0.50 0.60 0.70 \
  --n 100 \
  --backend ollama \
  --model mistral
```

## Output

- `data/revision/fix_04/per_query.csv`
- `results/revision/fix_04/tau_summary.csv`
- `results/revision/fix_04/tau_transfer_matrix.csv`
- `results/revision/fix_04/generalization_flags.csv`

## Result

Source package:

- `Downloads/fix3_4_t4x2_outputs.zip`

Verified output:

- Total rows: `7500`.
- Five datasets: SQuAD, PubMedQA, HotpotQA, Natural Questions, TriviaQA.
- Five tau values: `0.30`, `0.40`, `0.50`, `0.60`, `0.70`.
- Three conditions: baseline, HCPC-v1, CCS gate.
- Error rows: `0`.

Best diagonal tau by tune dataset:

| tune dataset | tau | diagonal recovery | off-diagonal mean | flag |
| --- | ---: | ---: | ---: | --- |
| pubmedqa | 0.4 | 1.452374 | 0.450586 | yes |
| naturalqs | 0.5 | 1.401456 | 0.210749 | yes |
| squad | 0.3 | 0.822675 | -0.140768 | yes |
| triviaqa | 0.4 | 0.463880 | 0.697710 | no |
| hotpotqa | 0.3 | -0.111786 | 0.092847 | no |

Interpretation: tau generalization is uneven. The paper must explicitly flag
the diagonal-vs-offdiagonal gaps for PubMedQA, NaturalQS, and SQuAD. HotpotQA
is a weak/null case for the CCS gate under this grid.
