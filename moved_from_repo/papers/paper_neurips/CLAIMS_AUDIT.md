# Claims Audit

This document records the safe claim boundary for the review-version
paper.

## Allowed Claims

- ControlledRAG is a prescriptive minimum reporting standard for RAG
  faithfulness claims.
- ControlledRAG turns a single-score RAG faithfulness claim into an
  auditable seven-axis evidence standard: generator, retriever, context
  structure, scorer, human calibration, threshold transfer, and cost.
- Fixed-generation metric fragility is observed on Mistral and persists
  in a compact Qwen2.5 replication.
- Raw scorer contrasts are score-scale dependent; standardized Mistral
  contrasts remain scorer-sensitive.
- The n = 99 human panel is a calibration and reliability check, not a
  settled scorer ranking.
- Answer-span presence and CCS carry complementary diagnostic signal in
  the matched SQuAD/Mistral cell.
- Retriever identity is an audit axis; stronger retriever checks are
  sanity checks rather than exhaustive robustness evidence.
- The long-form stress test is exploratory only.
- Threshold transfer is uneven and includes sign-changing normalized
  contrast cells.
- No audited method dominates across faithfulness, hallucination,
  latency, and indexing cost.

## Forbidden Claims

- CCS causes faithfulness.
- CCS drives faithfulness.
- HCPC-v2 solves hallucination.
- HCPC-v2 dominates.
- Self-RAG is globally weak.
- The Qwen2.5 replication proves universal generator robustness.
- The long-form stress test establishes broad generalization.
- Human evaluation establishes any scorer as universally reliable.
- ControlledRAG certifies faithful outputs.

## Wording Rule

Use "audit", "calibration", "reference human label set", "reliability
check", "suggestive", and "scoped" for evidence boundaries. Avoid
causal or universal language unless the paper reports an experiment that
directly supports it.
