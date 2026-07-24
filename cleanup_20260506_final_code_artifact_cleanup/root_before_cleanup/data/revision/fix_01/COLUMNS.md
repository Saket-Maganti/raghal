# Fix 1 column documentation

## `data/revision/fix_01/matched_pairs.csv`

One row per constructed query pair.

| column | description |
| --- | --- |
| `pair_id` | Stable SHA-1 based identifier for the query pair. |
| `dataset` | Dataset name; preregistered primary cell is `squad`. |
| `query_index` | Index of the QA pair in the loaded dataset list before shuffling. |
| `question` | Original query. |
| `ground_truth` | Reference answer when available. |
| `seed` | Query-shuffling seed. |
| `n_candidates` | Number of retrieved passages available; must be at least 20. |
| `n_triples_evaluated` | Number of enumerated 3-passage triples, normally C(20,3)=1140. |
| `bucket_id`, `bucket_size` | Similarity bucket selected by the combinatorial search. |
| `high_idxs`, `low_idxs` | JSON lists of source ranks from the top-20 retrieval pool. |
| `high_passages_json`, `low_passages_json` | JSON lists of the three passage texts used for generation. |
| `mean_sim_high`, `mean_sim_low` | Mean query-passage cosine similarity for each triple. |
| `sim_gap` | Absolute mean-similarity gap; preregistered maximum is 0.02. |
| `ccs_high`, `ccs_low`, `ccs_gap` | Context Coherence Score values and gap. |
| `overlap` | Number of shared passages between HIGH and LOW triples; maximum is 1. |
| `top20_*_query_sim` | Diagnostics over the full retrieved top-20 pool. |
| `construction_version` | Version label for the matching algorithm. |

## `data/revision/fix_01/per_query.csv`

Two rows per generated query pair, one for `high_ccs` and one for `low_ccs`.

| column | description |
| --- | --- |
| `pair_id`, `dataset`, `query_index`, `question`, `ground_truth`, `seed` | Pair metadata copied from `matched_pairs.csv`. |
| `model`, `backend` | Generator and serving backend. |
| `set_type` | `high_ccs` or `low_ccs`. |
| `passage_idxs` | JSON source ranks in the top-20 pool. |
| `mean_query_sim`, `ccs`, `sim_gap`, `ccs_gap`, `overlap` | Matching diagnostics. |
| `answer` | Generated answer from the three-passage context. |
| `faithfulness_score` | DeBERTa-v3 NLI mean entailment score. |
| `is_hallucination` | Boolean thresholded at faithfulness < 0.5. |
| `nli_label` | Detector label (`faithful` or `hallucinated`). |
| `latency_s` | Generator invocation latency. |
| `error` | Empty on success; populated for failed generation/scoring rows. |

## `data/revision/fix_01/skipped_queries.csv`

One row per attempted query that did not yield a matched pair, with `reason`.
