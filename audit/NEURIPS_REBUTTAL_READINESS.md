# NeurIPS Rebuttal Readiness

## Ready for low-risk clarification

- Submitted baseline identity and Git commit can be stated precisely.
- Existing source traces, manifests, requirements, scripts, consolidated results, and human-evaluation material can be mapped to reviewer questions.
- The documented `run_all_analysis.sh` workflow passed in 3.1 seconds in a temporary copy and reproduced the n=99 and n=100 human-calibration values.
- Existing bounded evidence directly supports clarifications on the seven-axis rationale, scorer input formats, the two human slices, threshold transfer, cost cells, a Qwen2.5 second-generator probe, stronger-embedder diagnostics, and the 40-question long-form limitation.

## Highest-value rebuttal opportunities

1. **Metric and human-calibration clarification:** explain answer-only versus context-conditioned inputs, random versus targeted human slices, and the submitted `average_precision_score` AUPRC convention.
2. **Scope clarification:** lead with the explicit narrow-surface limitation; describe Qwen2.5, retriever, HotpotQA, and long-form results as bounded probes, not broad generalization.
3. **Seven-axis rationale:** point to the existing “reasonable substitution can change the conclusion” criterion and soften any implication that seven is uniquely exhaustive.
4. **Evidence map:** provide exact paths/sample sizes for each reviewer concern using `CLAIMS_AUDIT.md`, `SOURCE_TRACE.md`, and `controlledrag_reporting_checklist.md`.
5. **If time permits:** validate full per-query inputs for the most contested table and recompute it without model calls.

## Not yet ready for scientific assertion

- Remnant outputs have not been proven to originate from the submitted code/configuration.
- The cleanup and submitted AUPRC implementations/results conflict; the submitted values reproduce, but mixing versions would be a factual error.
- The submitted artifact omits most full per-query outputs; the cleanup tree has 127 matching paths that require provenance validation.
- No completed contradictory-context experiment or modern-judge experiment is present.
- Four optional experiment scripts fail Python compilation.
- Full paper claim-to-result-to-command trace has not been manually verified.
- Lightweight checks cannot establish experimental correctness.

## Highest-value immediate work

Validate the paper’s most reviewer-relevant tables against full per-query files, generating scripts, configs, and hashes. This is higher-value and lower-risk than launching a new model experiment before provenance is settled.
