# ContextCoherenceBench (benchmark staging)

This directory is the **staging root** for the ContextCoherenceBench
release artifacts. Packaging is driven by `scripts/package_benchmark.py`,
which copies the current run outputs into a HuggingFace-loadable layout at
`release/context_coherence_bench_v1/`.

## Directory layout after packaging

```
release/context_coherence_bench_v1/
├── README.md                    # HuggingFace dataset card (auto-written)
├── CITATION.bib
├── LICENSE
├── metadata.json
├── adversarial/
│   ├── disjoint.jsonl           # 10 cases
│   ├── contradict.jsonl         # 10 cases
│   ├── drift.jsonl              # 10 cases
│   ├── control.jsonl            # 10 cases
│   └── README.md
├── coherence_paradox/
│   ├── per_query.csv            # (dataset, condition, query) rows
│   └── summary.csv              # (dataset, condition) aggregates
└── human_faithfulness/
    ├── aggregated.csv           # per-task majority labels + means
    └── manifest.csv             # provenance + NLI scores
```

## Release checklist

1. Adversarial: all 4 subsets populated (see `data/adversarial/*.jsonl`).
2. Coherence-paradox: `results/multidataset/per_query.csv` exists.
3. Human eval: `results/human_validation/study_v1/aggregated_annotations.csv`
   exists (after Prolific ingestion + analysis).
4. Run `python3 scripts/package_benchmark.py` with matching flags.
5. Inspect `metadata.json` — every `sha256` should be non-empty and
   `subsets[*].files[*].n_cases|n_rows|n_items` should match the expected
   counts listed in the paper.
6. `huggingface-cli upload <hf-namespace>/context-coherence-bench
    release/context_coherence_bench_v1 --repo-type dataset`.
7. Tag the git commit with `bench-v1` and cut a GitHub release pointing to
   the same SHA.

## Licensing summary

- Hand-authored adversarial cases: **CC-BY-4.0**.
- Per-dataset query content inherits upstream license (SQuAD: CC-BY-SA-4.0,
  PubMedQA: MIT, NaturalQuestions: CC-BY-SA-3.0, TriviaQA: Apache-2.0,
  HotpotQA: CC-BY-SA-4.0, FinanceBench: CC-BY-NC-4.0).
- Human annotation ratings: **CC-BY-4.0** with annotator IDs redacted.

## Not included

- Model weights (baseline / HCPC-v2 / CRAG / Self-RAG).
- The ChromaDB vector indices (regenerable from the ingestion scripts).
- Prolific annotator-level raw exports (privacy).
