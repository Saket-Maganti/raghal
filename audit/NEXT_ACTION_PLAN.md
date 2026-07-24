# Next Action Plan

## P0: Integrity and factual blockers

1. **Validate paper claim/table/figure provenance.** Trace every headline paper value through `rag-hallucination-detection_main/SOURCE_TRACE.md`, `rag-hallucination-detection_main/artifact_manifest.md`, generating scripts, configs, and hashed outputs. Dependencies: no new model runs; use the manifests and per-query files. Estimate: 4–12 CPU-hours. Risk: high if mappings disagree. Addresses source-trace, missing per-query, and factual-integrity concerns. Does not change claims unless a mismatch is found.
2. **Adjudicate logical scientific conflicts.** Start with `audit/LOGICAL_SNAPSHOT_CONFLICTS.csv`, `scripts/analyze_human_disagreement_labels.py`, and `results/revision/fix_03/disagreement_alignment_n100.csv`. Confirm the submitted `average_precision_score` convention and prohibit use of stale cleanup AUPRC values. Estimate: 2–4 CPU-hours; no GPU. Risk: mixing 0.886 and 0.859 RAGAS AUPRC values. Addresses metric-definition and factual-integrity concerns; clarification should not change the submitted claim.
3. **Manually clear publication/license holds.** Review `audit/EXCLUDED_FILES_MANIFEST.csv`, `audit/SECRET_SCAN_SUMMARY.md`, and `audit/LICENSE_AND_REDISTRIBUTION_NOTES.md`; rotate any real credential. Estimate: 1–3 hours. No compute. Does not change scientific claims.
4. **Correct documentation/source-trace contradictions on a later branch.** Resolve the missing `audit_log.md`, the checklist statement that `run_all_analysis.sh` regenerates every table, the absent `scripts/package_benchmark.py`, and the planned-but-omitted fix-09 results. Estimate: 3–8 CPU-hours; no GPU. Risk: editing the preserved baseline instead of a repair branch. Addresses reproducibility and code-navigation concerns; may narrow reproducibility claims.

## P1: NeurIPS rebuttal-critical clarifications/analyses

1. Map reviewer concerns to exact existing evidence using `audit/REVIEW_AND_META_REVIEW_CONCERN_MATRIX.md` and validate uncertainty at per-query level. Estimate: 4–10 CPU-hours. Low scientific risk if limited to verified outputs; no claim change unless corrections are required.
2. Validate scorer-to-human calibration and disagreement files under `rag-hallucination-detection_main/human_eval_final/`, `rag-hallucination-detection_main/results/revision/fix_03/`, and corresponding cleanup-tree paths. Estimate: 4–12 CPU-hours; no GPU expected. Addresses calibration and scorer-input interpretation.
3. Extract the smallest defensible cost, generator, retriever, and stress-test analyses from verified existing outputs. Estimate: 4–8 CPU-hours. No new claim until provenance is complete.

## P2: Fastest credible new experiments

1. Re-run only lightweight deterministic analyses whose inputs are already present (confidence intervals, error slices, threshold-transfer checks). Estimate: 2–8 CPU-hours. Risk: version skew; pin exact input hashes. May strengthen or narrow claims.
2. If credentials/compute are approved, run one current judge on a fixed, pre-hashed sample with explicit input formatting. Estimate: 2–8 GPU/API-hours. Risk: cost, nondeterminism, evaluator leakage. Adds a scoped new claim.

## P3: EACL-strengthening experiments

1. Validate and extend recovered long-form/multi-hop/stress, alternate-generator, alternate-retriever, and conflicting-evidence pipelines. Exact candidate paths are in `audit/RECOVERABLE_MISSING_EVIDENCE.md`. Estimate: 1–5 GPU-days plus API cost. Medium/high integrity risk until remnant provenance is resolved. Expands scientific scope.
2. Add modern judges, task-specific evaluators, repeated seeds, scorer-to-human calibration, threshold transfer, and full cost reporting. Estimate: 2–10 GPU-days/API equivalent. Changes and broadens claims.

## P4: Repository cleanup and paper rewrite

1. On a new branch, create one canonical package layout, locked environment, deterministic entry points, tests, and a claim-to-artifact map. Preserve `rag-hallucination-detection_main/` unchanged. Estimate: 2–5 engineer-days. No GPU. Does not itself change claims.
2. Rewrite metric/dataset/experiment descriptions and practitioner guidance only after P0–P3 evidence is stable. Estimate: 2–4 researcher-days. Claims may be clarified or narrowed, never retrofitted to unverified remnants.
