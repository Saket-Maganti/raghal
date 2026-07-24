# ContextCoherenceBench v2

Expansion of the v1 benchmark released alongside the NeurIPS 2026 submission
*"The Coherence Paradox in Retrieval-Augmented Generation"*.

## What changed vs v1

- **Adversarial cases**: 42 total
  (was 40 in v1). Per category:
    - disjoint: 12
    - contradict: 10
    - drift: 10
    - control: 10
- **Coherence paradox CSV**: refreshed on 2026-04-24T19:27:15Z UTC with all
  currently-completed (dataset, model) tuples from
  `results/multidataset/coherence_paradox.csv`.

## Layout

```
context_coherence_bench_v2/
├── README.md
├── LICENSE
├── CITATION.bib
├── metadata.json            # sha256 digests for every file
├── leaderboard.yaml         # community-submitted results
├── adversarial/
│   ├── disjoint.jsonl
│   ├── contradict.jsonl
│   ├── drift.jsonl
│   └── control.jsonl
└── coherence_paradox/
    └── coherence_paradox.csv
```

## Loading

```python
from datasets import load_dataset
ds = load_dataset("json", data_files={
    "disjoint":   "adversarial/disjoint.jsonl",
    "contradict": "adversarial/contradict.jsonl",
    "drift":      "adversarial/drift.jsonl",
    "control":    "adversarial/control.jsonl",
})
```

See `CITATION.bib` for how to cite.
