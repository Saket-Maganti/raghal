# Fix 7 Log - Independent 70B Reproduction

**Status:** code written; execution blocked in zero-dollar mode unless free
70B compute becomes available.  
**Weakness addressed:** W7, frontier result depends on one served backend.

## Protocol

- Dataset: SQuAD.
- Model: Together.ai `meta-llama/Llama-3.3-70B-Instruct-Turbo` if budget/API
  access is later allowed.
- Sample: `n=100`, seed `42`.
- Conditions: baseline and HCPC-v1.
- Pass criterion: paradox magnitude within `+/-0.02` of the frontier reference.
- Suspicious exact matches are explicitly flagged for rerun.

## Zero-Dollar Decision

Do not run this script under the current no-spend constraint. A 70B model does
not fit on the M4 Air or ordinary free T4/P100/L4 notebook sessions. The paper
should mark this reproduction as not completed under the revision budget rather
than imply it was verified.

## Command

```bash
TOGETHER_API_KEY=... python3 experiments/fix_07_together_70b_reproduction.py \
  --n 100 \
  --reference_magnitude 0.100
```

## Output

- `data/revision/fix_07/per_query.csv`
- `results/revision/fix_07/together_summary.csv`
- `results/revision/fix_07/together_reference_comparison.csv`
