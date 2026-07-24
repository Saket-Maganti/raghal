# ControlledRAG Reporting Checklist (filled-in template)

> **Note.** This is the ControlledRAG seven-axis reporting checklist for the
> frozen audit in this artifact. It is included so reviewers can map the
> reported values to the corresponding verification files.

| Axis | What this artifact reports |
| --- | --- |
| **Generator** | Mistral-$7$B-Instruct via local Ollama; greedy decoding; outputs frozen before scoring; second-generator probe with Qwen$2.5$-$7$B at $n{=}100$ fixed contexts per condition (one model, sanity check). |
| **Retriever** | `sentence-transformers/all-MiniLM-L6-v2` embedder + ChromaDB index; `cross-encoder/ms-marco-MiniLM-L-6-v2` reranker; three retrieval conditions (no-refinement / aggressive-refinement / gated-refinement, prior names HCPC-v$1$ / HCPC-v$2$); embedder sanity check vs.\ BGE-large and E5-large. |
| **Context structure** | CCS (mean$-$std of off-diagonal pairwise cosine sims), mean query similarity, answer-span lexical indicator; matched-context HIGH/LOW pairs at fixed mean similarity (similarity gap $\leq 0.02$). |
| **Scorer** | Three scorers on the same fixed generations: legacy DeBERTa-v$3$ zero-shot label proxy, legacy `roberta-large-mnli` zero-shot label proxy, RAGAS-style local Mistral judge (context-conditioned). Cross-scorer Pearson correlations reported. Context-conditioned NLI rescoring on a $600$-row balanced subset is frozen in `results/revision/context_conditioned_nli/`. |
| **Human calibration** | Two completed slices: typical-row calibration ($n{=}99$, two adjudicated passes, $\kappa=0.774$, raw agreement $0.919$, distribution $79/16/4$ supported / partially / unsupported, scorer$-$human Spearman $0.103/0.394/0.549$) and targeted disagreement slice ($n{=}100$, two raters plus adjudication, $\kappa=0.721$, raw agreement $0.88$, distribution $74/26/0$ faithful / hallucinated / unclear, scorer$-$human Spearman $-0.156/0.446/0.384$, AUROC $0.398/0.794/0.718$). Slice-dependent ranking. |
| **Threshold transfer** | $\tau$ swept over $\{0.3, 0.4, 0.5, 0.6, 0.7\}$ on five datasets (SQuAD, PubMedQA, HotpotQA, NaturalQuestions, TriviaQA); $5{\times}5$ recovery transfer matrix; sign-changing cells flagged. No bootstrap CIs. |
| **Cost** | Per-condition mean latency (ms), indexing time (s), and external-call assumptions for $n{=}200$ per cell on SQuAD and HotpotQA across CRAG, gated-refinement, and RAPTOR-$2$L; CRAG harness uses the documented evaluator with web search disabled (zero external calls in this run). |

## How to use this template in another paper

1. Copy this file under your repository as
   `controlledrag_reporting_checklist.md`.
2. Replace each entry in the right-hand column with the values that
   describe your audit.
3. Cite ControlledRAG and ship the filled-in checklist alongside
   your supplement.
4. If you cannot report a row, leave it blank or write
   "not reported"; that absence is itself disclosure.

The standard does not score papers; it asks reviewers to ask one
targeted question per axis.
