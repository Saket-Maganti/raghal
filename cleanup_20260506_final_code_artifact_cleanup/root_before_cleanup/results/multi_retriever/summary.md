# Multi-retriever ablation (Item #8)

Tests whether the refinement paradox is a property of context coherence
or merely a property of a weak embedder. We hold the generator (Mistral-7B),
the chunk size (1024), top-k (3), and the NLI scorer constant; the only
varied quantity is the dense retriever embedding model.

## Embedders

| Short name | Model | Params | Dim | Query prefix | Family |
|------------|-------|--------|-----|--------------|--------|
| `minilm` | sentence-transformers/all-MiniLM-L6-v2 | 22M | 384 | `(none)` | sentence-transformers |
| `bge-large` | BAAI/bge-large-en-v1.5 | 335M | 1024 | `Represent this sentence for searching relevant passages: ` | bge |
| `e5-large` | intfloat/e5-large-v2 | 335M | 1024 | `query: ` | e5 |
| `gte-large` | thenlper/gte-large | 335M | 1024 | `(none)` | gte |

## Aggregated metrics (per dataset × embedder × condition)

| dataset   | embedder   | condition   |   n_queries |   faith |   halluc |    sim |   refine_rate |      ccs |   latency |
|:----------|:-----------|:------------|------------:|--------:|---------:|-------:|--------------:|---------:|----------:|
| pubmedqa  | bge-large  | baseline    |          30 |  0.6112 |   0.2333 | 0.6986 |        0      | nan      |   11.0683 |
| pubmedqa  | bge-large  | hcpc_v1     |          30 |  0.5783 |   0.2333 | 0.6959 |        0      | nan      |    6.3667 |
| pubmedqa  | bge-large  | hcpc_v2     |          30 |  0.6061 |   0.1667 | 0.6982 |        0.9667 |   0.6387 |    9.4403 |
| pubmedqa  | e5-large   | baseline    |          30 |  0.6077 |   0.1667 | 0.8319 |        0      | nan      |   12.9523 |
| pubmedqa  | e5-large   | hcpc_v1     |          30 |  0.5552 |   0.2333 | 0.8344 |        0      | nan      |    8.0817 |
| pubmedqa  | e5-large   | hcpc_v2     |          30 |  0.5944 |   0.1667 | 0.8319 |        0.0333 |   0.7881 |   10.874  |
| pubmedqa  | gte-large  | baseline    |          30 |  0.5872 |   0.2    | 0.8502 |        0      | nan      |   12.7287 |
| pubmedqa  | gte-large  | hcpc_v1     |          30 |  0.5817 |   0.2    | 0.8571 |        0      | nan      |    7.3577 |
| pubmedqa  | gte-large  | hcpc_v2     |          30 |  0.5837 |   0.1333 | 0.8502 |        0      |   0.7629 |   10.402  |
| pubmedqa  | minilm     | baseline    |          30 |  0.5913 |   0.1667 | 0.5166 |        0      | nan      |   11.3967 |
| pubmedqa  | minilm     | hcpc_v1     |          30 |  0.5674 |   0.2667 | 0.5471 |        0      | nan      |    6.4887 |
| pubmedqa  | minilm     | hcpc_v2     |          30 |  0.5867 |   0.2    | 0.5168 |        0.9667 |   0.3091 |    9.841  |
| squad     | bge-large  | baseline    |          30 |  0.8098 |   0.0667 | 0.6589 |        0      | nan      |    4.6463 |
| squad     | bge-large  | hcpc_v1     |          30 |  0.7778 |   0      | 0.6601 |        0      | nan      |    3.113  |
| squad     | bge-large  | hcpc_v2     |          30 |  0.803  |   0.0333 | 0.6588 |        0.4333 |   0.6669 |    4.9007 |
| squad     | e5-large   | baseline    |          30 |  0.815  |   0.0333 | 0.8193 |        0      | nan      |    4.5397 |
| squad     | e5-large   | hcpc_v1     |          30 |  0.8263 |   0      | 0.8213 |        0      | nan      |    2.1923 |
| squad     | e5-large   | hcpc_v2     |          30 |  0.8345 |   0.0333 | 0.8193 |        0      |   0.7729 |    3.0623 |
| squad     | gte-large  | baseline    |          30 |  0.8048 |   0      | 0.8773 |        0      | nan      |    4.3187 |
| squad     | gte-large  | hcpc_v1     |          30 |  0.8062 |   0      | 0.8807 |        0      | nan      |    1.7597 |
| squad     | gte-large  | hcpc_v2     |          30 |  0.7999 |   0      | 0.8773 |        0      |   0.8522 |    2.562  |
| squad     | minilm     | baseline    |          30 |  0.7797 |   0      | 0.5877 |        0      | nan      |    3.8723 |
| squad     | minilm     | hcpc_v1     |          30 |  0.7044 |   0.1667 | 0.6008 |        0      | nan      |    2.9993 |
| squad     | minilm     | hcpc_v2     |          30 |  0.8038 |   0      | 0.5879 |        0.5333 |   0.5425 |    4.327  |

## Headline: paradox magnitude per embedder

`paradox_drop` = faith_baseline − faith_v1 (positive ⇒ refinement hurt)
`v2_recovery`  = faith_v2 − faith_v1       (positive ⇒ coherence-preserving
                                            probe restored faithfulness)

| dataset   | embedder   |   embedder_params |   faith_baseline |   faith_v1 |   faith_v2 |   paradox_drop |   v2_recovery |   halluc_baseline |   halluc_v1 |   halluc_v2 |   sim_baseline |   sim_v1 |
|:----------|:-----------|------------------:|-----------------:|-----------:|-----------:|---------------:|--------------:|------------------:|------------:|------------:|---------------:|---------:|
| pubmedqa  | bge-large  |         335000000 |           0.6112 |     0.5783 |     0.6061 |         0.0329 |        0.0278 |            0.2333 |      0.2333 |      0.1667 |         0.6986 |   0.6959 |
| pubmedqa  | e5-large   |         335000000 |           0.6077 |     0.5552 |     0.5944 |         0.0525 |        0.0392 |            0.1667 |      0.2333 |      0.1667 |         0.8319 |   0.8344 |
| pubmedqa  | gte-large  |         335000000 |           0.5872 |     0.5817 |     0.5837 |         0.0055 |        0.002  |            0.2    |      0.2    |      0.1333 |         0.8502 |   0.8571 |
| pubmedqa  | minilm     |          22000000 |           0.5913 |     0.5674 |     0.5867 |         0.0239 |        0.0193 |            0.1667 |      0.2667 |      0.2    |         0.5166 |   0.5471 |
| squad     | bge-large  |         335000000 |           0.8098 |     0.7778 |     0.803  |         0.032  |        0.0252 |            0.0667 |      0      |      0.0333 |         0.6589 |   0.6601 |
| squad     | e5-large   |         335000000 |           0.815  |     0.8263 |     0.8345 |        -0.0113 |        0.0082 |            0.0333 |      0      |      0.0333 |         0.8193 |   0.8213 |
| squad     | gte-large  |         335000000 |           0.8048 |     0.8062 |     0.7999 |        -0.0014 |       -0.0063 |            0      |      0      |      0      |         0.8773 |   0.8807 |
| squad     | minilm     |          22000000 |           0.7797 |     0.7044 |     0.8038 |         0.0753 |        0.0994 |            0      |      0.1667 |      0      |         0.5877 |   0.6008 |

## Interpretation guide

- If `paradox_drop` is positive across ALL embedders ⇒ coherence framing
  survives the strong-retriever critique; the failure mode is general.
- If `paradox_drop` shrinks to ~0 for the 335M models ⇒ the paper must
  reframe as 'failure mode of weak retrievers' (still a real result, but
  scope changes).
- `v2_recovery` should remain positive across all embedders if HCPC-v2
  is a genuine coherence-preserving intervention.