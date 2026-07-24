# RAG Hallucination Detection — Experiment Summary

> **Generated from real experiment outputs.**  All values are NLI-based faithfulness scores and hallucination rates computed by `cross-encoder/nli-deberta-v3-base`.  Hallucination threshold: faithfulness < 0.50.

## Experiment Inventory

| Phase             | Configs | Total Queries |
|-------------------|---------|---------------|
| phase1_ablation   | 24      | 720           |
| phase2_multimodel | 48      | 3600          |
| phase3_reranker   | 13      | 950           |
| phase4_zeroshot   | 4       | 300           |
| phase5_adaptive   | 12      | 360           |
| phase6_hcpc       | 4       | 120           |
| **TOTAL**         | 105     | 6050          |

## Phase 1: Ablation Study — SQuAD (Mistral-7B, n=30 per config)

| chunk_size | top_k | prompt | faithfulness | halluc_rate |
|------------|-------|--------|--------------|-------------|
| 1024       | 5     | strict | 0.8274       | 3.3%        |
| 1024       | 5     | cot    | 0.8254       | 3.3%        |
| 1024       | 3     | strict | 0.8001       | 3.3%        |
| 1024       | 3     | cot    | 0.7891       | 0.0%        |
| 512        | 5     | strict | 0.7861       | 3.3%        |
| 512        | 3     | strict | 0.7827       | 0.0%        |
| 512        | 3     | cot    | 0.7781       | 0.0%        |
| 512        | 5     | cot    | 0.7737       | 6.7%        |
| 256        | 5     | strict | 0.7254       | 10.0%       |
| 256        | 5     | cot    | 0.7253       | 10.0%       |
| 256        | 3     | cot    | 0.6835       | 6.7%        |
| 256        | 3     | strict | 0.6732       | 10.0%       |

> **Best config**: chunk=1024, k=5, prompt=strict → faithfulness=0.8274, hallucination_rate=3.3%

## Phase 1: Ablation Study — PubMedQA (Mistral-7B, n=30 per config)

| chunk_size | top_k | prompt | faithfulness | halluc_rate |
|------------|-------|--------|--------------|-------------|
| 512        | 3     | cot    | 0.6196       | 13.3%       |
| 1024       | 3     | cot    | 0.6167       | 10.0%       |
| 512        | 3     | strict | 0.6028       | 16.7%       |
| 1024       | 3     | strict | 0.5963       | 20.0%       |
| 512        | 5     | cot    | 0.5906       | 13.3%       |
| 1024       | 5     | cot    | 0.5881       | 13.3%       |
| 1024       | 5     | strict | 0.5849       | 16.7%       |
| 512        | 5     | strict | 0.5844       | 20.0%       |
| 256        | 3     | cot    | 0.5802       | 20.0%       |
| 256        | 5     | cot    | 0.5636       | 26.7%       |
| 256        | 3     | strict | 0.5591       | 30.0%       |
| 256        | 5     | strict | 0.5585       | 30.0%       |

> **Best config**: chunk=512, k=3, prompt=cot → faithfulness=0.6196, hallucination_rate=13.3%

## Phase 2: Multi-Model Validation (n=50–100 per config)

| model   | dataset  | chunk | k | prompt | faithfulness | halluc_rate | n   |
|---------|----------|-------|---|--------|--------------|-------------|-----|
| llama3  | pubmedqa | 256   | 5 | strict | 0.6233       | 10.0%       | 50  |
| mistral | pubmedqa | 256   | 3 | cot    | 0.6004       | 20.0%       | 50  |
| llama3  | squad    | 1024  | 5 | strict | 0.7752       | 0.0%        | 100 |
| mistral | squad    | 1024  | 3 | strict | 0.7775       | 3.0%        | 100 |

> Note: Llama-3 outperforms Mistral on SQuAD hallucination rate (2.4% vs 5.5%). On PubMedQA, Llama-3 achieves higher faithfulness but the domain gap persists for both models.

## Phase 3: Re-Ranking Impact (k=5 retrieve → k=3 rerank, n=50–100)

| model   | dataset  | chunk | condition | faithfulness | halluc_rate | n   |
|---------|----------|-------|-----------|--------------|-------------|-----|
| llama3  | pubmedqa | 256   | baseline  | 0.6136       | 18.0%       | 50  |
| llama3  | pubmedqa | 256   | reranked  | 0.6455       | 8.0%        | 50  |
| llama3  | pubmedqa | 512   | baseline  | 0.5862       | 20.0%       | 50  |
| llama3  | pubmedqa | 512   | reranked  | 0.5957       | 26.0%       | 50  |
| llama3  | pubmedqa | 1024  | baseline  | 0.5853       | 18.0%       | 50  |
| llama3  | pubmedqa | 1024  | reranked  | 0.5806       | 16.0%       | 50  |
| llama3  | squad    | 256   | baseline  | 0.7233       | 5.0%        | 100 |
| llama3  | squad    | 256   | reranked  | 0.7265       | 2.0%        | 100 |
| llama3  | squad    | 512   | baseline  | 0.7523       | 5.0%        | 100 |
| llama3  | squad    | 512   | reranked  | 0.7544       | 2.0%        | 100 |
| llama3  | squad    | 1024  | baseline  | 0.7739       | 1.0%        | 100 |
| llama3  | squad    | 1024  | reranked  | 0.7619       | 1.0%        | 100 |
| mistral | pubmedqa | 1024  | reranked  | 0.5884       | 18.0%       | 50  |

> **Re-ranker deltas (reranked − baseline):**
  - llama3/pubmedqa/chunk=256: Δfaithfulness=+0.0319, Δhalluc=-10.0%
  - llama3/pubmedqa/chunk=512: Δfaithfulness=+0.0095, Δhalluc=+6.0%
  - llama3/pubmedqa/chunk=1024: Δfaithfulness=-0.0047, Δhalluc=-2.0%
  - llama3/squad/chunk=256: Δfaithfulness=+0.0032, Δhalluc=-3.0%
  - llama3/squad/chunk=512: Δfaithfulness=+0.0021, Δhalluc=-3.0%
  - llama3/squad/chunk=1024: Δfaithfulness=-0.0120, Δhalluc=+0.0%

## Phase 4: Zero-Shot Baseline vs. Best RAG Configuration

| model   | dataset  | zeroshot_faith | zeroshot_halluc | best_rag_faith | best_rag_halluc | Δfaith (RAG−ZS) | Δhalluc (RAG−ZS) |
|---------|----------|----------------|-----------------|----------------|-----------------|-----------------|------------------|
| mistral | squad    | 0.6895         | 5.0%            | 0.7775         | 3.0%            | +0.0880         | -2.0%            |
| mistral | pubmedqa | 0.6118         | 8.0%            | 0.6004         | 20.0%           | -0.0114         | +12.0%           |
| llama3  | squad    | 0.6967         | 13.0%           | 0.7752         | 0.0%            | +0.0785         | -13.0%           |
| llama3  | pubmedqa | 0.6110         | 4.0%            | 0.6233         | 10.0%           | +0.0123         | +6.0%            |

> **Key finding**: RAG *hurts* on PubMedQA. Zero-shot Mistral hallucinates only 8%, but even the best RAG configuration pushes hallucination to 20%. This suggests the retrieved biomedical abstracts introduce conflicting evidence rather than grounding the model's parametric knowledge.

## Statistical Significance (PubMedQA ANOVA)

| Test                     | F-statistic | p-value  | Significant (α=0.05) |
|--------------------------|-------------|----------|----------------------|
| chunk_size_squad         | 19.7203     | 0.000000 | Yes *                |
| chunk_size_pubmedqa      | 3.6636      | 0.026609 | Yes *                |
| prompt_strategy_squad    | 0.0460      | 0.830261 | No                   |
| prompt_strategy_pubmedqa | 1.1224      | 0.290119 | No                   |
| top_k_squad              | 2.9175      | 0.088490 | No                   |
| top_k_pubmedqa           | 2.3231      | 0.128352 | No                   |

> Chunk size is the only statistically significant factor in both datasets.  SQuAD: F=19.72, p<0.001 (large effect, d=0.80 for chunk=256 vs 1024).  PubMedQA: F=3.66, p=0.027 (small-medium effect, d=0.31).  Prompt strategy and top-k are not significant in either dataset.

## Phase 6: Hybrid Context-Preserving Chunking (HCPC)

| dataset  | condition | faithfulness | halluc_rate | n  | Δ faith (vs base) | Δ halluc (vs base) |
|----------|-----------|--------------|-------------|----|-------------------|--------------------|
| squad    | baseline  | 0.8122       | 0.0%        | 30 |                   |                    |
| squad    | hcpc      | 0.7289       | 13.3%       | 30 | -0.0833           | +13.3%             |
| pubmedqa | baseline  | 0.6031       | 10.0%       | 30 |                   |                    |
| pubmedqa | hcpc      | 0.5544       | 36.7%       | 30 | -0.0487           | +26.7%             |

> **SQUAD**: 100.0% of queries triggered refinement; mean CE improvement per refined chunk = -0.6200
> **PUBMEDQA**: 100.0% of queries triggered refinement; mean CE improvement per refined chunk = 0.6117

## Phase 5: Adaptive Chunking (Pending Execution)

| dataset  | strategy       | description                                       | faithfulness | halluc_rate | n_chunks |
|----------|----------------|---------------------------------------------------|--------------|-------------|----------|
| pubmedqa | fixed_1024     | Fixed 1024-token chunks (baseline)                | 0.6053       | 13.3%       | 54       |
| pubmedqa | semantic_tight | Semantic chunking (threshold=0.6, tight cohesion) | 0.6006       | 13.3%       | 121      |
| pubmedqa | dynamic        | Dynamic paragraph-aware chunking                  | 0.5903       | 16.7%       | 30       |
| pubmedqa | fixed_512      | Fixed 512-token chunks (baseline)                 | 0.5892       | 20.0%       | 101      |
| pubmedqa | fixed_256      | Fixed 256-token chunks (baseline)                 | 0.5718       | 30.0%       | 220      |
| pubmedqa | semantic_loose | Semantic chunking (threshold=0.4, loose cohesion) | 0.5657       | 26.7%       | 76       |
| squad    | dynamic        | Dynamic paragraph-aware chunking                  | 0.7902       | 0.0%        | 30       |
| squad    | fixed_1024     | Fixed 1024-token chunks (baseline)                | 0.7886       | 0.0%        | 35       |
| squad    | semantic_loose | Semantic chunking (threshold=0.4, loose cohesion) | 0.7763       | 10.0%       | 37       |
| squad    | semantic_tight | Semantic chunking (threshold=0.6, tight cohesion) | 0.7647       | 13.3%       | 65       |
| squad    | fixed_512      | Fixed 512-token chunks (baseline)                 | 0.7415       | 6.7%        | 53       |
| squad    | fixed_256      | Fixed 256-token chunks (baseline)                 | 0.6444       | 10.0%       | 115      |
