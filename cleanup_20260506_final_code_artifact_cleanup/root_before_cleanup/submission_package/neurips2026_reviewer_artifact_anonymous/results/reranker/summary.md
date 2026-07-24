# Reranker Experiment — Summary

N_DOCS=30, N_QUESTIONS=30, MODEL=llama3, CHUNK=1024, TOP_K=3, FETCH_K=7

## SQUAD

| Condition | Faithfulness | Halluc. Rate | Mean CE Score | Latency |
|-----------|:----------:|:----------:|:----------:|:------:|
| baseline | 0.8326 | 0.0% | 0.0 | 5.149s |
| reranker | 0.8295 | 0.0% | 3.8205 | 3.534s |
| hcpc_v2 | 0.8192 | 0.0% | 0.0 | 4.392s |
| hcpc_v2_rr | 0.8235 | 0.0% | 0.0 | 4.354s |

## PUBMEDQA

| Condition | Faithfulness | Halluc. Rate | Mean CE Score | Latency |
|-----------|:----------:|:----------:|:----------:|:------:|
| baseline | 0.5844 | 23.3% | 0.0 | 14.353s |
| reranker | 0.568 | 20.0% | 1.8899 | 14.328s |
| hcpc_v2 | 0.596 | 10.0% | 0.0 | 16.893s |
| hcpc_v2_rr | 0.5811 | 20.0% | 0.0 | 16.403s |

