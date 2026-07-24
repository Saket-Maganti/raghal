# Artifact Manifest

This manifest describes the reviewer-facing code artifact:
`submission_package/neurips2026_reviewer_artifact_anonymous.zip`.

## Top-Level Files

| Path | Purpose |
| --- | --- |
| `README.md` | concise artifact overview and quick start |
| `README_REPRODUCE.md` | detailed reproduction instructions |
| `requirements.txt` | lightweight analysis dependencies |
| `requirements-full.txt` | optional full experiment dependency set |
| `run_all_analysis.sh` | lightweight verification entry point |
| `controlledrag_reporting_checklist.md` | ControlledRAG reporting checklist |
| `SOURCE_TRACE.md` | maps paper claims to source files |
| `CLAIMS_AUDIT.md` | numerical claim audit |
| `artifact_manifest.md` | this manifest |

## Verification Scripts

| Path | Purpose |
| --- | --- |
| `scripts/verify_human_eval.py` | verifies the `n=99` human-evaluation calibration |
| `scripts/analyze_human_disagreement_labels.py` | verifies the `n=100` targeted disagreement slice |
| `scripts/compute_standardized_scorer_fragility.py` | optional scorer-fragility check |
| `scripts/compute_matched_ccs_distribution.py` | optional matched HIGH/LOW CCS check |
| `scripts/compute_cost_headtohead_cis.py` | optional cost-aware interval check |
| `scripts/compute_nli_human_correlation.py` | optional context-conditioned NLI alignment summary |

## Frozen Results

| Path | Purpose |
| --- | --- |
| `human_eval_final/n99_calibration/` | final `n=99` annotation and verification files |
| `human_eval_final/n100_disagreement/` | final `n=100` targeted disagreement files |
| `results/revision/fix_01/` | matched context-structure audit |
| `results/revision/fix_02/` | scaled audit summaries |
| `results/revision/fix_03/` | scorer-fragility and human-calibration summaries |
| `results/revision/context_conditioned_nli/` | context-conditioned NLI rescoring outputs |
| `results/revision/fix_04/` | threshold-transfer matrix |
| `results/revision/fix_05/` | coherence-vs-noise summaries |
| `results/revision/fix_06/` | cost-aware head-to-head summaries |
| `results/revision/fix_11/` | RAPTOR-2L cost table |
| `results/revision/fix_12/` | answer-span/control diagnostic |
| `results/revision/fix_13/` | stronger-retriever sanity check |
| `results/revision/fix_14/` | second-generator probe summaries |
| `results/revision/fix_15/` | long-form stress summaries |
| `results/multi_retriever/` | stronger-retriever summary files |
| `source_tables/` | compact table inputs |

The default verification path uses the final files under
`human_eval_final/`. Optional cost-aware checks use
`data/revision/fix_06/per_query_compact.csv`, a numeric projection of the
full local per-query file.

## Excluded From Reviewer ZIP

- paper PDFs and paper source
- public demos and release links
- revision notes, internal runbooks, and assistant-specific files
- caches, logs, notebook checkpoints, and operating-system metadata
- compiled TeX auxiliary files
- local absolute paths and personal identifiers

This artifact is only for code and reproducibility checks.
