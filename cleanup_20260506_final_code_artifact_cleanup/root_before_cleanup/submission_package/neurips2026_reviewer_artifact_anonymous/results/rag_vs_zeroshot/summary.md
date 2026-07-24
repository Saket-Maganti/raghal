# RAG vs zero-shot (NeurIPS Gap 3)

Answers the reviewer question: *does retrieval help, and under what conditions?*  Reshapes existing `results/zeroshot/`, `results/multi_retriever/`, and `results/multidataset/` outputs — no new LLM calls.

Domain split: `open` = SQuAD / HotpotQA / TriviaQA / NaturalQS, `closed` = PubMedQA.  
Retriever strength split: `weak` = MiniLM-L6 (22 M params), `strong` = GTE-large / BGE-large / E5-large (335 M params).

## Headline 2×2 (domain × retriever strength)

`delta_faith` = faith(RAG, baseline condition) − faith(zero-shot).  Positive = RAG helps.  `rag_helps` flags the sign.

| domain   | retriever_strength   |   n_datasets | embedders_used   |   zs_faith |   rag_faith |   delta_faith | rag_helps   |   paradox_drop |   v2_recovery |
|:---------|:---------------------|-------------:|:-----------------|-----------:|------------:|--------------:|:------------|---------------:|--------------:|
| open     | weak                 |            1 | minilm           |     0.6895 |      0.7797 |        0.0902 | True        |         0.0753 |        0.0994 |
| open     | strong               |            1 | gte-large        |     0.6895 |      0.8048 |        0.1153 | True        |        -0.0014 |       -0.0063 |
| closed   | weak                 |            1 | minilm           |     0.6118 |      0.5913 |       -0.0205 | False       |         0.0239 |        0.0193 |
| closed   | strong               |            1 | gte-large        |     0.6118 |      0.5872 |       -0.0246 | False       |         0.0055 |        0.002  |

## Does the coherence paradox depend on retriever strength?

`mean_paradox_drop` is the average faith drop from baseline to HCPC-v1 across datasets at that retriever strength.  A strength-invariant paradox is strong evidence that the effect is driven by the LM's coherence preference rather than by retriever noise.

| retriever_strength   |   n_cells |   mean_paradox_drop |   std_paradox_drop |   mean_v2_recovery |   mean_delta_faith |
|:---------------------|----------:|--------------------:|-------------------:|-------------------:|-------------------:|
| strong               |         6 |              0.0184 |             0.0245 |             0.016  |             0.0553 |
| weak                 |         2 |              0.0496 |             0.0363 |             0.0593 |             0.0348 |

## Per-cell detail

One row per (dataset, embedder).  `paradox_drop` = faith_baseline − faith_v1.  `v2_recovery` = faith_v2 − faith_v1.

| model   | dataset   | domain   | embedder   | retriever_strength   |   zs_faith |   rag_faith |   delta_faith | rag_helps   |   zs_halluc |   rag_halluc |   rag_sim |   rag_latency |   paradox_drop |   v2_recovery |
|:--------|:----------|:---------|:-----------|:---------------------|-----------:|------------:|--------------:|:------------|------------:|-------------:|----------:|--------------:|---------------:|--------------:|
| mistral | pubmedqa  | closed   | bge-large  | strong               |     0.6118 |      0.6112 |       -0.0006 | False       |        0.08 |       0.2333 |    0.6986 |        11.068 |         0.0329 |        0.0278 |
| mistral | pubmedqa  | closed   | e5-large   | strong               |     0.6118 |      0.6077 |       -0.0041 | False       |        0.08 |       0.1667 |    0.8319 |        12.952 |         0.0525 |        0.0392 |
| mistral | pubmedqa  | closed   | gte-large  | strong               |     0.6118 |      0.5872 |       -0.0246 | False       |        0.08 |       0.2    |    0.8502 |        12.729 |         0.0055 |        0.002  |
| mistral | pubmedqa  | closed   | minilm     | weak                 |     0.6118 |      0.5913 |       -0.0205 | False       |        0.08 |       0.1667 |    0.5166 |        11.397 |         0.0239 |        0.0193 |
| mistral | squad     | open     | bge-large  | strong               |     0.6895 |      0.8098 |        0.1203 | True        |        0.05 |       0.0667 |    0.6589 |         4.646 |         0.032  |        0.0252 |
| mistral | squad     | open     | e5-large   | strong               |     0.6895 |      0.815  |        0.1255 | True        |        0.05 |       0.0333 |    0.8193 |         4.54  |        -0.0113 |        0.0082 |
| mistral | squad     | open     | gte-large  | strong               |     0.6895 |      0.8048 |        0.1153 | True        |        0.05 |       0      |    0.8773 |         4.319 |        -0.0014 |       -0.0063 |
| mistral | squad     | open     | minilm     | weak                 |     0.6895 |      0.7797 |        0.0902 | True        |        0.05 |       0      |    0.5877 |         3.872 |         0.0753 |        0.0994 |