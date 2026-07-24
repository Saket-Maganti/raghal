---
language:
  - en
license: cc-by-4.0
task_categories:
  - question-answering
  - text-classification
tags:
  - rag
  - retrieval-augmented-generation
  - hallucination
  - faithfulness
  - context-coherence
pretty_name: ContextCoherenceBench v1
size_categories:
  - n<1K
---

# ContextCoherenceBench v1

Companion benchmark for *“When Retrieval Improvements Hurt: Context
Coherence and Faithfulness in Retrieval-Augmented Generation.”*

The benchmark targets a specific empirical regularity we call the
**context coherence paradox**: naive retrieval improvements that raise
per-passage relevance can *lower* generation faithfulness because the
resulting passage set is more fragmented. ContextCoherenceBench lets other
researchers reproduce that effect on their own retrievers / generators and
compare against our selective-refinement baseline (HCPC-v2) as well as
Self-RAG and CRAG.

## Tasks

### 1. `adversarial_coherence`
- **N = 40** hand-authored cases.
- Four subsets:
  - `disjoint.jsonl` (10): passages all relevant to the query but drawn
    from disjoint topical neighborhoods.
  - `contradict.jsonl` (10): relevant passages containing contradictory
    claims about the queried entity.
  - `drift.jsonl` (10): passages that drift from a near-miss topic to the
    true target.
  - `control.jsonl` (10): matched coherent controls.
- **Schema** (one JSON per line):
  ```
  {
    "case_id":  str,
    "category": "disjoint"|"contradict"|"drift"|"control",
    "question": str,
    "passages": [str, ...],
    "expected_failure_mode": str,
    "notes":    str
  }
  ```
- **Target metric**: per-signal detection AUC across {mean_query_chunk_sim,
  CCS, mean_jaccard, embedding_variance, retrieval_entropy, sim_spread,
  nli_pairwise_\{mean,max,frac_hi\}}. See Table 4 in the paper.

### 2. `coherence_paradox`
- **N ≈ 630** queries across six datasets (SQuAD, PubMedQA,
  NaturalQuestions, TriviaQA, HotpotQA, FinanceBench).
- **Conditions**: baseline, hcpc_v1, hcpc_v2, crag, selfrag.
- **Schema**: `per_query.csv` columns —
  `dataset, condition, question, ground_truth, answer,
   faithfulness_score, is_hallucination, mean_retrieval_similarity,
   latency_s`.
- **Target metric**: paradox_drop = faith(baseline) − faith(hcpc_v1);
  v2_recovery = faith(hcpc_v2) − faith(hcpc_v1).

### 3. `human_faithfulness`
- **N = TBD** (case, condition) items, 2 annotators each via
  Prolific (1000 annotation tasks).
- **Schema**: `aggregated.csv` —
  `task_id, n_annotations, human_faithful_rate, majority_faithful,
   mean_correctness, mean_helpfulness, any_disagreement`.
  Joined with `manifest.csv` for condition / NLI / provenance.
- **Target metric**: Fleiss' kappa (binary + ordinal) and Spearman
  rho(NLI faithfulness, human_faithful_rate).

## Provenance
- Adversarial cases: authored by the paper author; CC-BY-4.0.
- Coherence-paradox queries: drawn from the upstream datasets under their
  original licenses; see `metadata.json` for per-dataset details.
- Human annotations: collected on Prolific under IRB-exempt protocol
  (described in §6.X). Annotator IDs are redacted to `A<n>`.

## Loading

```python
from datasets import load_dataset

# Adversarial subset
adv = load_dataset("<hf-namespace>/context-coherence-bench",
                    name="adversarial_coherence")

# Coherence-paradox subset
par = load_dataset("<hf-namespace>/context-coherence-bench",
                    name="coherence_paradox")
```

## Baselines

Reproduction scripts ship in the companion GitHub repo:

```
git clone https://github.com/<anonymized>/context-coherence-bench
python3 experiments/run_adversarial_coherence.py
python3 experiments/run_multidataset_validation.py
python3 experiments/run_headtohead_comparison.py
```

## Citation

```bibtex
@inproceedings{maganti2026coherence,
  title     = {When Retrieval Improvements Hurt: Context Coherence and
               Faithfulness in Retrieval-Augmented Generation},
  author    = {Maganti, Saket},
  booktitle = {Proceedings of EMNLP / ACL 2026 (under review)},
  year      = {2026},
}
```

Version: v1  (packaged 2026-04-24)
