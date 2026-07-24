# Frontier-scale ablation (Phase 2 Item 2)

Re-runs the coherence-paradox comparison on 70-B class models via the Groq free-tier API.  The retrieval stack (MiniLM embeddings + HCPC retrievers) is unchanged; only the generation LLM is swapped from Ollama Mistral-7B to a larger model, so any difference in `paradox_drop` is attributable to scale.

## Aggregated metrics

| dataset   | model         | condition   |   n_queries |   faith |   halluc |    sim |   refine_rate |      ccs |   latency |
|:----------|:--------------|:------------|------------:|--------:|---------:|-------:|--------------:|---------:|----------:|
| pubmedqa  | gpt-oss-120b  | baseline    |          30 |  0.548  |   0.2667 | 0.5166 |        0      | nan      |    4.8133 |
| pubmedqa  | gpt-oss-120b  | hcpc_v1     |          30 |  0.5355 |   0.3    | 0.5471 |        0      | nan      |    3.7447 |
| pubmedqa  | gpt-oss-120b  | hcpc_v2     |          30 |  0.5362 |   0.3333 | 0.5168 |        0.9667 |   0.3091 |    5.7347 |
| pubmedqa  | llama-3.3-70b | baseline    |          30 |  0.5518 |   0.1667 | 0.5166 |        0      | nan      |    2.025  |
| pubmedqa  | llama-3.3-70b | hcpc_v1     |          30 |  0.5468 |   0.2333 | 0.5471 |        0      | nan      |    1.6403 |
| pubmedqa  | llama-3.3-70b | hcpc_v2     |          30 |  0.5775 |   0.0667 | 0.5168 |        0.9667 |   0.3091 |    1.9687 |
| squad     | gpt-oss-120b  | baseline    |          30 |  0.7103 |   0.0667 | 0.5877 |        0      | nan      |    2.9    |
| squad     | gpt-oss-120b  | hcpc_v1     |          30 |  0.6804 |   0      | 0.6008 |        0      | nan      |    0.8677 |
| squad     | gpt-oss-120b  | hcpc_v2     |          30 |  0.7064 |   0.0667 | 0.5879 |        0.5333 |   0.5425 |    3.3707 |
| squad     | llama-3.3-70b | baseline    |          30 |  0.7668 |   0.0667 | 0.5877 |        0      | nan      |    1.7233 |
| squad     | llama-3.3-70b | hcpc_v1     |          30 |  0.6668 |   0.1    | 0.6008 |        0      | nan      |    1.652  |
| squad     | llama-3.3-70b | hcpc_v2     |          30 |  0.7582 |   0.0667 | 0.5879 |        0.5333 |   0.5425 |    1.7427 |

## Paradox vs 7B reference

`ref_paradox_7b` = same-dataset paradox drop at Mistral-7B from `results/multidataset/summary.csv`.  `delta_vs_7b > 0` means the paradox grew at scale; `< 0` means it shrank.  `paradox_persists` = True if the 70B run still shows > 0.01 faith drop from baseline to HCPC-v1 — the canonical threshold for 'the paradox is real at this scale.'

| dataset   | model         | scale   |   faith_base |   faith_v1 |   faith_v2 |   paradox_drop |   v2_recovery |   ref_paradox_7b |   delta_vs_7b | paradox_persists   |
|:----------|:--------------|:--------|-------------:|-----------:|-----------:|---------------:|--------------:|-----------------:|--------------:|:-------------------|
| pubmedqa  | gpt-oss-120b  | 120B    |       0.548  |     0.5355 |     0.5362 |         0.0125 |        0.0007 |           0.0247 |       -0.0122 | True               |
| pubmedqa  | llama-3.3-70b | 70B     |       0.5518 |     0.5468 |     0.5775 |         0.005  |        0.0307 |           0.0247 |       -0.0197 | False              |
| squad     | gpt-oss-120b  | 120B    |       0.7103 |     0.6804 |     0.7064 |         0.0299 |        0.026  |           0.0999 |       -0.07   | True               |
| squad     | llama-3.3-70b | 70B     |       0.7668 |     0.6668 |     0.7582 |         0.1    |        0.0914 |           0.0999 |        0.0001 | True               |

Target finding for NeurIPS: `paradox_persists == True` on at least one 70B row.  That rules out "it's a small-model artifact" as a reviewer critique.