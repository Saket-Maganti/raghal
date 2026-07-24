# Shared Facts and Numbers

## Use rule

This is the common fact surface for Prompt 6. Reviewer responses may shorten
these facts, but may not broaden them. Numerical claims must remain within the
P0 gate and the row-specific safety language in the claim ledger.

## Scope

- ControlledRAG is a practical disclosure and audit procedure. The seven
  categories are not mathematically unique or formally exhaustive.
- Numerical conclusions are bounded primarily to short-answer QA and
  7B-class local generators.
- Additional breadth is diagnostic rather than universal validation:
  a five-dataset threshold grid, two-dataset cost comparison, bounded
  retriever checks, one Qwen2.5-7B probe, and an exploratory 40-question
  MS-MARCO/QASPER panel.
- The framework can be instantiated in other RAG settings as a method, but
  its numerical effects and rankings are not established to transfer to
  agentic, broad long-form, or modern-judge settings.

## Experiment inventory

| Cell | Verified description | Evidence grade |
| --- | --- | --- |
| Matched context | SQuAD, 200 HIGH/LOW matched pairs; Mistral-7B; MiniLM/Chroma; legacy DeBERTa answer-only proxy | Medium; one dataset and scorer |
| Scorer comparison | SQuAD fixed 7,500-row table, 2,500 rows per condition; seeds 41–45; two legacy answer-only proxies and a custom RAGAS-style judge | Strong for audited fixed rows |
| Scorer input format | Balanced fixed 600-row subset; 194 complete baseline/HCPC-v1 pairs per context-conditioned backbone | Strong sensitivity demonstration; not scorer validation |
| Typical human calibration | Separate `n=99` slice, 33 rows per condition | Medium; small and only four adjudicated unsupported rows |
| Disagreement-targeted human calibration | Separate `n=100` slice, 34/33/33 rows by condition | Medium; targeted diagnostic, not prevalence |
| Threshold transfer | PubMedQA, Natural Questions, SQuAD, TriviaQA, HotpotQA; 5×5 fixed grid | Diagnostic; descriptive only |
| Cost | SQuAD and HotpotQA; three systems × 200 rows per dataset | Conditional; hardware-specific point estimates |
| Retriever | SQuAD/PubMedQA pilot, 720 generated rows; separate 1,200-row fixed-context re-encoding panel | Exploratory/diagnostic |
| Second generator | Qwen2.5-7B, 100 contexts per condition, 300 rows | Exploratory; one additional generator |
| Long form | 20 MS-MARCO + 20 QASPER questions, three conditions, 120 rows | Weak/exploratory |

## Metric definitions

- **Legacy DeBERTa proxy:** answer-sentence-only zero-shot probability for the
  label “entailment”; retrieved context is not consumed. Higher is treated as
  more faithful; row aggregation averages sentence scores.
- **Legacy second NLI proxy:** whole-answer-only zero-shot entailment-label
  probability in the default historical branch. It is not context-conditioned
  ground truth.
- **RAGAS-style judge:** custom local question+context+answer prompt producing
  a scalar in `[0,1]`. It is not the official `ragas` package and not human
  ground truth.
- **Context-conditioned NLI:** retrieved context is the premise and answer
  sentences are hypotheses. This is a more direct calling convention, not a
  universally correct scorer.
- **Average precision:** `sklearn.metrics.average_precision_score` with
  `faithful=1` and higher scores indicating faithfulness. Do not substitute
  the stale historical “AUPRC” computation.

## Human evaluation

- Two raters labeled independently before reconciliation; disagreements were
  adjudicated afterward.
- Agreement uses pre-adjudication labels; scorer alignment uses adjudicated
  labels.
- Typical slice (`n=99`): raw agreement `0.919192`, unweighted Cohen’s kappa
  `0.773779`.
- Disagreement-targeted slice (`n=100`): raw agreement `0.880000`, kappa
  `0.720930`.
- The two slices have different selection designs and label schemas and are
  never pooled.
- On `n=99`, adjudicated-ordinal Spearman correlations are `0.103`, `0.394`,
  and `0.549` for legacy DeBERTa, the second legacy NLI proxy, and the
  RAGAS-style judge.
- On `n=100`, the corresponding Spearman correlations are `-0.156`, `0.446`,
  and `0.384`; the last two are not reliably ordered.
- On the separate `n=100` faithful-positive binary endpoint, sklearn average
  precision is `0.764813 / 0.928793 / 0.859367`.
- There is no verified same-row human comparison between answer-only and
  context-conditioned NLI. Do not imply one.

## Figure 2 / scorer-input sensitivity

The 600 answers and contexts are fixed; no retrieval or generation changes.
For 194 complete baseline/HCPC-v1 pairs, the mean baseline-minus-HCPC-v1
contrast changes from `+0.017` to `-0.279` for DeBERTa and from `+0.044` to
`-0.081` for the second NLI backbone when the call changes from answer-only
label prediction to context-as-premise NLI. Paired bootstrap intervals support
the reversal on this fixed panel. This demonstrates input-format sensitivity,
not that context-conditioned NLI is universally correct.

## Practitioner protocol

1. Specify the deployment decision, population, endpoint, positive class, and
   cost constraints.
2. Disclose all seven categories, using “not varied” or “not measured” where
   appropriate.
3. Lock output origin: generated, rescored, re-encoded, imported, or
   aggregated.
4. Calibrate on a deployment-relevant human slice.
5. Stress-test only reasonable alternatives that can change sign, rank,
   threshold choice, or deployment decision.
6. Classify findings as stable, conditional, or unresolved.
7. For multi-objective choices, remove point-estimate-dominated systems,
   declare weights/constraints, and retain a conditional Pareto set when no
   robust winner exists.

This is guidance, not a prospectively validated universal aggregation rule.

## Conflicting retrieved evidence

Verified citation:

> Arie Cattan et al. “DRAGged into Conflicts: Detecting and Addressing
> Conflicting Sources in Search-Augmented LLMs.” arXiv:2506.08500, 2025.

That work studies conflict among retrieved sources. ControlledRAG’s scorer
disagreement result concerns measurement choices applied to fixed outputs.
These are distinct. The current audit has no completed contradictory-context
experiment and must not imply otherwise.

## Modern-judge versions

### Version A — recommended now

No new modern-judge result is needed or claimed. The current evidence uses two
legacy answer-only proxies, one custom RAGAS-style judge, fixed-output
context-conditioned NLI, and two separate human-calibration slices. We
explicitly scope the absence of broader judge families as a limitation.

### Version B — insertion template only; do not use now

> After a separately authorized run, we evaluated [immutable model/revision]
> on the pre-frozen [candidate size] fixed-output sample. The valid run
> retained [complete pairs] and yielded a paired baseline-minus-HCPC-v1
> contrast of [estimate] with 95% CI [lower, upper]. This is fixed-output
> rescoring, not fresh retrieval/generation or ground truth.

Version B remains unusable unless a later run is separately authorized,
passes every ingestion gate, and is independently fact-checked.

## Judge status lock

`PROMPT_05_REPAIRED_PREPARED_NOT_EXECUTED`

Synthetic/adversarial tests: 58 passed, 0 failed. Network calls: 0. Model
loads/downloads: 0. Real rows scored: 0.
