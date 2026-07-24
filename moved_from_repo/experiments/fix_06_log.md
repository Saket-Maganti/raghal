# Fix 6 Log - Proper Baseline Head-To-Head

**Status:** no-Self-RAG Kaggle T4 x 2 run complete; Self-RAG optional follow-up pending.  
**Weakness addressed:** W6, RAPTOR/Self-RAG/CRAG comparison too thin.

## Protocol

- Datasets: SQuAD and HotpotQA.
- Sample: `n>=200` per dataset.
- Conditions implemented in the same harness:
  - HCPC-v2;
  - CRAG;
  - RAPTOR-2L.
  - Self-RAG when `--include_selfrag` is passed. This should be run on a CUDA
    host because it loads the fine-tuned Self-RAG checkpoint.

## Command

```bash
python3 experiments/fix_06_baseline_h2h_pareto.py \
  --datasets squad hotpotqa \
  --n 200 \
  --backend ollama \
  --model mistral
```

CUDA Self-RAG variant:

```bash
python3 experiments/fix_06_baseline_h2h_pareto.py \
  --datasets squad hotpotqa \
  --n 200 \
  --backend ollama \
  --model mistral \
  --include_selfrag \
  --selfrag_8bit
```

## Output

- `data/revision/fix_06/per_query.csv`
- `results/revision/fix_06/h2h_summary.csv`
- `results/revision/fix_06/pareto_faithfulness_latency.pdf`

## Remaining Execution Plan

Fresh Kaggle T4 x2 notebook and wrappers have been added:

- `notebooks/revision_fix6_kaggle_t4x2_fresh.ipynb`
- `scripts/kaggle_fix6_t4x2.sh`
- `scripts/kaggle_stream_fix6_t4x2.py`

The no-Self-RAG path has been imported. Attempt the Self-RAG smoke test and
full Self-RAG run only if the smoke test passes. The experiment script writes
periodic partial CSVs via `--save_every`.

## Result

The no-Self-RAG path of Fix 6 ran successfully on Kaggle T4 x 2 and was
imported from `AAA_FIX6_T4X2_OUTPUTS.zip`. The Self-RAG smoke test and
full Self-RAG run were not attempted in that session; they remain
optional follow-ups.

Sample: 2 datasets (SQuAD, HotpotQA) x 3 conditions (CRAG, HCPC-v2,
RAPTOR-2L) x 200 queries = 1200 evaluations.

Head-to-head summary (results/revision/fix_06/h2h_summary.csv):

| dataset  | condition | n   | faithfulness | hallucination_rate | mean_latency_ms | p99_latency_ms | base_index_s | raptor_index_s |
| -------- | --------- | --: | -----------: | -----------------: | --------------: | -------------: | -----------: | -------------: |
| squad    | crag      | 200 | 0.6982       | 0.120              | 1440.49         | 5110.87        | 8.01         | 175.35         |
| squad    | hcpc_v2   | 200 | 0.7084       | 0.125              | 1719.94         | 5399.50        | 8.01         | 175.35         |
| squad    | raptor_2l | 200 | 0.7100       | 0.125              | 1713.70         | 4441.73        | 8.01         | 175.35         |
| hotpotqa | crag      | 200 | 0.6427       | 0.105              | 1940.65         | 4254.93        | 7.97         | 134.01         |
| hotpotqa | hcpc_v2   | 200 | 0.6334       | 0.125              | 2288.94         | 5545.37        | 7.97         | 134.01         |
| hotpotqa | raptor_2l | 200 | 0.6308       | 0.130              | 2413.58         | 5074.35        | 7.97         | 134.01         |

Pareto plot at results/revision/fix_06/pareto_faithfulness_latency.pdf;
copied to ragpaper/figures/fix_06_pareto_faith_latency.pdf for the
paper.

Honest interpretation: HCPC-v2 does NOT clearly dominate the head-to-
head. On SQuAD, HCPC-v2 (0.7084 faith, 12.5% halluc) is essentially
tied with RAPTOR-2L (0.7100 faith, 12.5% halluc) and slightly above
CRAG (0.6982 faith, 12.0% halluc), with all three within a 1.2 pp
band. On HotpotQA, CRAG wins on both faithfulness (0.6427) and
hallucination rate (10.5%) and is the fastest (1940 ms mean latency),
while HCPC-v2 (0.6334 faith, 12.5% halluc, 2289 ms) is dominated.

Indexing cost is the other practical wedge: RAPTOR's offline tree-
build is 134-175 s vs. dense indexing at 8 s, a 17-22x cost premium
that has to be amortized across many queries.

Combined with the Fix 1 null and the Fix 2 paradox collapse, Fix 6
weakens the v2.0 paper claim that HCPC-v2 is a controlled instrument
that recovers faithfulness against strong baselines. The honest paper
language is "HCPC-v2 is competitive on SQuAD but not on HotpotQA, and
no method clearly dominates within a 1-2 pp faith band."

Self-RAG smoke test and full Self-RAG run remain pending and are
optional follow-ups via `notebooks/revision_fix6_kaggle_t4x2_fresh.ipynb`
stages `smoke_selfrag` and `selfrag` respectively.
