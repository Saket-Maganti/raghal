# Fix 11 Log - RAPTOR Full Table

**Status:** complete; result generated and locally available.  
**Weakness addressed:** W11, RAPTOR was only mentioned in one line.

## Protocol

- Datasets: SQuAD, PubMedQA, HotpotQA by default.
- RAPTOR: two-level tree with one summary layer.
- Metrics: faithfulness, hallucination rate, p50/p99 latency, dense index
  build time, RAPTOR tree build time, index size.

## Command

```bash
python3 experiments/fix_11_raptor_full_table.py \
  --datasets squad pubmedqa hotpotqa \
  --n 100 \
  --backend ollama \
  --model mistral
```

## Output

- `data/revision/fix_11/per_query.csv`
- `results/revision/fix_11/raptor_full_table.csv`
- `results/revision/fix_11/raptor_indexing_costs.csv`

## Result

- Total rows: `300`.
- Datasets: SQuAD, PubMedQA, HotpotQA.

| dataset | n | faithfulness | hallucination_rate | p50 latency ms | p99 latency ms | dense index s | RAPTOR index s | index size MB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hotpotqa | 100 | 0.616708 | 0.210000 | 1972.55 | 4274.46 | 7.140 | 99.740 | 16.594 |
| pubmedqa | 100 | 0.560011 | 0.290000 | 3900.97 | 6811.90 | 1.177 | 108.264 | 3.102 |
| squad | 100 | 0.789326 | 0.050000 | 1190.46 | 4942.80 | 8.333 | 161.203 | 1.832 |

Interpretation: RAPTOR now has a full reportable table with faithfulness,
hallucination rate, latency, indexing cost, and index size.
