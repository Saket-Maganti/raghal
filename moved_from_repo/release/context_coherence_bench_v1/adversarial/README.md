# Adversarial Coherence Cases (§7.6)

Three categories of retrieval sets where standard relevance metrics give a
false "pass" signal but the context is structurally incoherent in a way that
provokes hallucination:

| File | Category | Construction rule |
|------|----------|-------------------|
| `disjoint.jsonl`    | Terminologically disjoint | Passages use different surface forms for the same entity. Jaccard between passages `< 0.08`; every passage has query-cosine `> 0.55`. |
| `contradict.jsonl`  | Internally contradictory | At least one passage pair with NLI-contradict probability `> 0.5`; all passages have query-cosine `> 0.55`. |
| `drift.jsonl`       | Topic drift               | `sim(p_i, p_{i+1}) > 0.6` for every adjacent pair, but `sim(p_1, p_k) < 0.4`. Every passage individually passes the per-chunk relevance threshold. |
| `control.jsonl`     | Coherent control          | Same queries as the adversarial cases, but the retrieval set is the unmodified top-k from the baseline pipeline on the full corpus. |

## Record schema

```json
{
  "case_id": "disjoint_001",
  "category": "disjoint",
  "query": "What is the main cause of myocardial infarction?",
  "corpus": "pubmedqa",
  "passages": [
    {"source_id": "PMID:12345", "text": "..."},
    ...
  ],
  "construction": {
    "selection_rule": "synonym_divergence",
    "min_query_sim": 0.55,
    "max_pairwise_jaccard": 0.08
  },
  "expected": {
    "relevance_flags_it": false,
    "coherence_flags_it": true,
    "primary_coherence_signal": "mean_jaccard"
  },
  "notes": "Passages use 'MI', 'heart attack', 'cardiac infarction' across chunks."
}
```

## Construction pipeline

1. Seed cases in `seeds/` (hand-authored by paper author) — primary source of
   truth for §7.6.
2. `scripts/expand_adversarial_cases.py` can extend each category using an
   LLM-in-the-loop approach for the benchmark release (Item C1). For the
   paper's main adversarial section, we use only the seed cases to avoid
   LLM-authoring contamination.

## Ground truth faithfulness

Each case has a hand-written reference answer and a `gold_context_label`
indicating whether the retrieval set, as assembled, actually contains a
defensible answer:

- `answerable`      — a faithful answer is constructible from the passages.
- `partial`         — the passages overlap the answer but disagree.
- `unanswerable`    — no consistent answer is derivable; model should abstain.

The model's output is judged against both the NLI-entailment score on the
passages *and* a reference-based correctness check.
