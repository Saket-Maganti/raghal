# Fix 5 Log - SQuAD Noise-Slope Response

**Status:** complete; result generated and locally available.  
**Weakness addressed:** W5, the old limitations section disclosed that random
noise could explain part of the SQuAD effect.

## Protocol

- Dataset: SQuAD.
- Sample: `n=200`, seed `42`.
- Conditions:
  - baseline;
  - random off-topic noise;
  - same-topic answer-absent noise from the query's top-20 pool;
  - HCPC-v1 refinement.
- Noise levels: replace `1`, `2`, or `3` of the top-3 passages.

## Interpretation

If same-topic answer-absent noise has a much smaller faithfulness slope than
random noise, and refinement remains worse at comparable similarity drop, the
paradox is not merely "the set got worse generally." If not, the robustness
section must say that the paradox is hard to separate from retrieval quality
degradation on SQuAD.

## Command

```bash
python3 experiments/fix_05_coherence_preserving_noise.py \
  --n 200 \
  --seed 42 \
  --backend ollama \
  --model mistral
```

## Output

- `data/revision/fix_05/per_query.csv`
- `results/revision/fix_05/noise_summary.csv`
- `results/revision/fix_05/slope_response.csv`

## Result

- Total rows: `1591`.
- Baseline faithfulness: `0.680252`.
- HCPC-v1 refinement faithfulness: `0.679045`.
- Random-noise faithfulness slope per noise rate: `-0.068592`.
- Coherent-uninformative-noise faithfulness slope per noise rate: `-0.043224`.
- Random-noise similarity slope per noise rate: `-0.481011`.
- Coherent-uninformative-noise similarity slope per noise rate: `-0.112631`.

Interpretation: coherent same-topic answer-absent noise causes a smaller
similarity collapse than random noise, but still lowers faithfulness. This
should be reported as robustness evidence with a careful limitation, not as a
complete dismissal of retrieval-quality degradation.
