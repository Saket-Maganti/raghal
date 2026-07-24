# Human-eval sampling report (Phase 7 #6)

Total: 90 samples
Boundary-oversample fraction: 0.3
Seed: 42

## Counts by (dataset, condition, nli_label)

| dataset | condition | nli_label | n |
| --- | --- | --- | --- |
| hotpotqa | baseline | faithful | 5 |
| hotpotqa | baseline | hallucinated | 1 |
| hotpotqa | hcpc_v1 | faithful | 5 |
| hotpotqa | hcpc_v1 | hallucinated | 1 |
| hotpotqa | hcpc_v2 | faithful | 5 |
| hotpotqa | hcpc_v2 | hallucinated | 1 |
| naturalqs | baseline | faithful | 6 |
| naturalqs | hcpc_v1 | faithful | 5 |
| naturalqs | hcpc_v1 | hallucinated | 1 |
| naturalqs | hcpc_v2 | faithful | 6 |
| pubmedqa | baseline | faithful | 5 |
| pubmedqa | baseline | hallucinated | 1 |
| pubmedqa | hcpc_v1 | faithful | 5 |
| pubmedqa | hcpc_v1 | hallucinated | 1 |
| pubmedqa | hcpc_v2 | faithful | 3 |
| pubmedqa | hcpc_v2 | hallucinated | 3 |
| squad | baseline | faithful | 6 |
| squad | hcpc_v1 | faithful | 6 |
| squad | hcpc_v2 | faithful | 6 |
| triviaqa | baseline | faithful | 5 |
| triviaqa | baseline | hallucinated | 1 |
| triviaqa | hcpc_v1 | faithful | 6 |
| triviaqa | hcpc_v2 | faithful | 4 |
| triviaqa | hcpc_v2 | hallucinated | 2 |

## Rater protocol
1. Read the question, ground truth, and generated answer.
2. Mark `human_label`: ``faithful`` if the answer is fully 
   supported by the question's standard evidence (the
   rater should be familiar with the dataset); 
   ``hallucinated`` otherwise.
3. Set `human_faith`: 1 if faithful, 0 if hallucinated.
4. Add free-text `notes` for ambiguous cases.
5. After rating: `python3 experiments/analyze_human_eval.py` 
   computes accuracy + Cohen's kappa vs NLI.