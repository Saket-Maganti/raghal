# Research Framing

## One-Sentence Claim

ControlledRAG is a prescriptive minimum reporting standard for RAG
faithfulness claims, validated by fixed-generation metric fragility,
human calibration, matched-context controls, second-generator
replication, retriever sanity checks, threshold transfer, and
cost-aware baselines.

## Headline Positioning

The strongest finding the paper now makes is methodological:
**RAG faithfulness claims are under-identified unless the generator,
retriever, context structure, evaluator, human calibration, threshold
transfer, and cost are reported separately.** The audit experiments
demonstrate the standard by self-applying it to our own prior
contribution.

## What Changed (vs. v2.0 longform paper)

The original framing treated context coherence as a mechanism that
drives faithfulness and HCPC-v2 as a recommended deployment policy.
The senior-reviewer revision does not support that causal language:

- The matched CCS intervention is null and has the wrong hallucination
  direction.
- The scaled SQuAD/Mistral headline contrast is small and seed-sensitive.
- Automated faithfulness scorers disagree by an order of magnitude on
  fixed generations.
- Stronger embeddings can flip the SQuAD paradox sign.
- Threshold transfer is uneven across datasets.
- The cost-aware head-to-head shows no dominating system.

The revised paper therefore treats the experiments as an audit of
under-identification in RAG evaluation, and positions ControlledRAG
as the positive contribution.

## What Survives as Positive Findings

- Fixed-generation scorer disagreement is strong and is replicated in
  ordering under a compact Qwen2.5 second-generator audit.
- Answer-bearing evidence presence is a useful positive diagnostic to
  report with CCS and mean query similarity. The joint feature set
  outperforms any single feature on both faithfulness R^2 and
  hallucination AUROC.
- Coherence-preserving noise produces a distinguishably smaller
  faithfulness drop than random off-topic noise at matched
  substitution rate.
- Two human raters reach substantial agreement (kappa 0.774) on the
  binary faithful/hallucinated label.
- Released artifacts remain runnable: pip package, HuggingFace
  Dataset, Zenodo DOI, LangChain integration, and an interactive
  demo.

## Paper Structure (target ~9-10 pages)

Main paper:
1. Introduction (under-identification thesis + ControlledRAG)
2. Background and related work
3. Setup and audited cells
4. ControlledRAG: minimum reporting standard
5. Matched-context audit + answer-span/control diagnostic
6. Scaled audit
7. Metric fragility (Mistral + Qwen2.5)
8. Human calibration
9. Threshold transfer
10. Coherence vs noise
11. Cost-aware baselines
12. Discussion
13. Related work, continued
14. Limitations and ethics
15. Conclusion

Supplement:
- Pre-registration
- Per-seed scaled-audit detail
- Answer-span/control full table
- Stronger retriever sanity check
- Second generator (Qwen2.5)
- Self-RAG harness-mismatched appendix baseline
- Noise full slopes
- Threshold transfer full sweep
- Human calibration protocol
- Source trace and artifact manifest
- Long-form stress test
- Resume / compute notes

## Non-Goals

- Do not propose HCPC-v2 as a generally superior system.
- Do not propose CCS as a causal mechanism or faithfulness oracle.
- Do not claim long-form generalization.
- Do not claim scorer validity beyond the reported agreement /
  correlation evidence.
- Do not claim that the second-generator audit proves universal
  generator robustness.
- Do not claim that the stronger-retriever sanity check proves
  retriever-agnostic results.
- Do not claim that Self-RAG is globally weak; we explicitly mark the
  Self-RAG row as a harness-mismatched appendix baseline.

## Allowed Phrasing

The positive contribution is a standard of evidence: RAG faithfulness
claims should not be accepted from a single retrieval score, a single
faithfulness scorer, a single tuned threshold, or a single favorable
baseline row.

## Forbidden Phrasing

- "CCS drives faithfulness"
- "CCS causes faithfulness"
- "HCPC-v2 solves hallucination"
- "HCPC-v2 dominates"
- "Self-RAG is globally weak"
- "Human eval validates RAGAS"
- "ControlledRAG certifies faithful outputs"
- "Long-form stress test validates the protocol broadly"
- "Second generator proves universal robustness"
- "Stronger retriever check proves robustness"
