# ControlledRAG: A Pre-Registered Audit and Minimum Reporting Standard for RAG Faithfulness Evaluation

This repository contains the anonymized reproducibility artifact for the ControlledRAG RAG faithfulness audit. It is prepared for double-blind review and contains only the code, frozen result tables, source traces, and human-evaluation artifacts needed to verify the reported claims. It intentionally omits paper PDFs, interactive demos, author-identifying links, and internal revision history.

## Project Overview

Retrieval-augmented generation (RAG) systems are often evaluated by a small number of aggregate faithfulness scores. ControlledRAG treats that as too thin for reliable reporting. The project asks a narrower and more reproducible question:

> When a RAG system changes retrieval quality, context structure, faithfulness scorer, or evaluation slice, which reported conclusions remain stable?

The artifact is built around controlled comparisons of short-answer extractive QA settings. The main objects of study are:

- retrieval conditions that change the structure and ranking of context passages,
- Context Coherence Score (CCS), a retrieval-time diagnostic of passage-to-passage coherence,
- automated faithfulness scorers that can disagree with one another,
- two human-evaluation slices used to calibrate and stress-test automated metrics,
- compact source tables that map reported claims to frozen CSVs.

The repository is not a service, demo, or full paper source tree. It is a reviewer-facing code artifact whose job is to make the reported numbers auditable.

## What ControlledRAG Reports

ControlledRAG follows a minimum reporting standard for RAG faithfulness evaluation. The included checklist records the major experimental axes:

- generator and decoding setup,
- retriever and refinement conditions,
- context-structure diagnostics,
- automated faithfulness scorers,
- human-calibration slices,
- threshold-transfer behavior,
- latency and cost assumptions.

The filled checklist is in `controlledrag_reporting_checklist.md`. Claim-level file pointers are in `SOURCE_TRACE.md` and `CLAIMS_AUDIT.md`.

## Main Frozen Findings

This artifact preserves the final numerical results used for the controlled audit. The short version is:

- **Matched-context audit:** at matched mean retrieval similarity, the HIGH-vs-LOW context-structure contrast is essentially null: faithfulness difference `-0.002`, paired Wilcoxon `p=0.628`, Cohen's `d_z=-0.017`, bootstrap CI `[-0.022, +0.017]`.
- **Scaled audit:** pooled faithfulness means for the three primary retrieval conditions are `0.661 / 0.650 / 0.661`, with hallucination rates `14.6% / 14.7% / 14.3%`.
- **Metric fragility:** the same fixed generations yield different effect magnitudes across scorers. The raw Mistral values are `0.011` for DeBERTa, `0.032` for a second NLI scorer, and `0.140` for the RAGAS-style local judge.
- **Context-conditioned NLI check:** context-conditioned scoring can reverse or shrink legacy scorer contrasts, which is why the artifact reports scorer setup explicitly.
- **Human calibration:** the typical-row slice has high rater agreement but weak-to-moderate scorer alignment; the targeted disagreement slice shows larger scorer separation and slice-dependent metric ranking.
- **Cost-aware comparison:** CRAG, gated refinement, and RAPTOR-2L are compared with faithfulness, hallucination, latency, and indexing-cost columns rather than only one accuracy score.

These are frozen results, not commands that regenerate large model generations by default.

## Repository Contents

- `README.md`: project overview and quick start
- `README_REPRODUCE.md`: detailed reproduction and troubleshooting instructions
- `SOURCE_TRACE.md`: mapping from reported claims to source files
- `CLAIMS_AUDIT.md`: claim-level numerical audit
- `artifact_manifest.md`: inventory of the reviewer artifact
- `controlledrag_reporting_checklist.md`: filled minimum reporting checklist
- `requirements.txt`: lightweight verification dependencies
- `requirements-full.txt`: optional dependencies for expensive regeneration scripts
- `run_all_analysis.sh`: default lightweight verification entry point
- `scripts/`: verification and derived-analysis scripts
- `src/`: reusable RAG, retrieval, scoring, and utility code
- `experiments/`: experiment entry points and optional regeneration scripts
- `data/`: small frozen data artifacts required by scripts
- `results/`: final frozen result tables used for claims
- `source_tables/`: compact CSVs behind selected reported tables
- `human_eval_final/`: final human-evaluation annotation and summary files
- `tests/`: smoke tests for core utilities
- `submission_package/`: regenerated anonymous reviewer artifact ZIP

## Quick Start

Use Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash run_all_analysis.sh
```

The default verification path is intentionally lightweight. It reads frozen CSVs and does not rerun retrieval, generation, or large model rescoring.

## Default Verification

`run_all_analysis.sh` runs:

```bash
python3 scripts/verify_human_eval.py
python3 scripts/analyze_human_disagreement_labels.py
```

Expected output for the typical-row human-evaluation slice:

- `n=99`
- raw agreement: `0.919`
- Cohen's kappa: `0.774`
- adjudicated distribution: `79/16/4`
- Spearman correlations: `0.103/0.394/0.549`

Expected output for the targeted disagreement slice:

- `n=100`
- raw agreement: `0.88`
- Cohen's kappa: `0.721`
- adjudicated distribution: `74/26/0`
- Spearman correlations: `-0.156/0.446/0.384`
- AUROC: `0.398/0.794/0.718`
- AUPRC: `0.765/0.929/0.859`

## Human-Evaluation Files

The final human-evaluation artifacts live under `human_eval_final/`.

`human_eval_final/n99_calibration/` contains the typical-row calibration slice:

- `human_eval_adjudicated.csv`
- `human_eval_n99_with_context.csv`
- `human_eval_summary.csv`
- `human_eval_label_distribution.csv`
- `human_eval_correlations.csv`
- `bootstrap_correlation_cis.csv`
- `human_eval_verification.csv`

`human_eval_final/n100_disagreement/` contains the targeted scorer-disagreement slice:

- `annotation_batch_disagreement_100.csv`
- `human_eval_rater1.csv`
- `human_eval_rater2.csv`
- `human_eval_adjudicated.csv`
- `human_disagreement_summary.csv`
- `human_disagreement_label_distribution.csv`
- `human_disagreement_agreement.csv`
- `human_disagreement_correlations.csv`
- `human_disagreement_auroc_auprc.csv`
- `human_disagreement_bootstrap_cis.csv`

These files are required final artifacts and should not be regenerated or edited during lightweight verification.

## Result File Map

The final public result tree is intentionally small.

- `results/revision/fix_01/`: matched-context structure audit
- `results/revision/fix_02/`: scaled audit summaries
- `results/revision/fix_03/`: scorer fragility and human-calibration summaries
- `results/revision/context_conditioned_nli/`: context-conditioned NLI rescoring outputs
- `results/revision/fix_04/`: threshold-transfer matrix
- `results/revision/fix_05/`: coherence-vs-noise summaries
- `results/revision/fix_06/`: cost-aware head-to-head summaries
- `results/revision/fix_11/`: RAPTOR-2L cost table
- `results/revision/fix_12/`: answer-span/control diagnostic
- `results/revision/fix_13/`: stronger-retriever sanity check
- `results/revision/fix_14/`: second-generator probe summaries
- `results/revision/fix_15/`: long-form stress summaries
- `results/multi_retriever/`: compact stronger-retriever summary files
- `source_tables/`: compact table inputs for selected diagnostics

For exact claim-to-file mappings, use `SOURCE_TRACE.md` first and `CLAIMS_AUDIT.md` for the numerical audit.

## Scripts

The main reviewer-facing scripts are:

- `scripts/verify_human_eval.py`: verifies the `n=99` human-evaluation calibration files
- `scripts/analyze_human_disagreement_labels.py`: recomputes the `n=100` targeted disagreement metrics
- `scripts/compute_standardized_scorer_fragility.py`: optional scorer-fragility check
- `scripts/compute_matched_ccs_distribution.py`: optional matched CCS distribution check
- `scripts/compute_cost_headtohead_cis.py`: optional cost-aware interval check
- `scripts/compute_nli_human_correlation.py`: optional context-conditioned NLI alignment check

The `experiments/` directory contains heavier experiment entry points. Those scripts are included for transparency and optional regeneration, but they are not part of the default reviewer path.

## Lightweight vs. Expensive Runs

The default path:

- uses frozen CSVs,
- runs on a laptop CPU,
- requires only `requirements.txt`,
- does not call paid APIs,
- does not rerun generation,
- does not rebuild vector stores.

Optional expensive scripts may require local model runtimes, embedding models, more memory, and substantially longer wall-clock time. Install `requirements-full.txt` only for that path.

## Anonymous Reviewer ZIP

The reviewer ZIP is:

```text
submission_package/neurips2026_reviewer_artifact_anonymous.zip
```

It contains only:

- root reproducibility docs,
- `scripts/`,
- `src/`,
- `experiments/`,
- `data/`,
- `results/`,
- `source_tables/`,
- `human_eval_final/`,
- `tests/`.

It excludes paper source, PDFs, demos, notebooks, release packaging, local caches, generated junk, and internal history.

## Troubleshooting

- Run commands from the repository root.
- If imports fail, activate the virtual environment and reinstall `requirements.txt`.
- If `run_all_analysis.sh` fails, run the two verification scripts separately to identify the missing input.
- If an optional experiment script fails because a large model or vector store is unavailable, use the frozen CSV verification path instead.
- If regenerated metrics differ, check whether the script is reading the final files under `human_eval_final/` and `results/revision/`.

## Scope Notes

This artifact supports reproducibility and auditing of the frozen results. It is not intended to be a general-purpose RAG framework, hosted benchmark service, or public demo. The repository is deliberately narrow so reviewers can inspect the code and verify the reported numbers without navigating paper drafts or private project history.
