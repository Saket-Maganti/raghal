# Cleanup Plan

This plan was written before moving or deleting repository files.

## Files and folders that will stay in the public artifact

- `README.md` with the required title:
  `ControlledRAG: A Pre-Registered Audit and Minimum Reporting Standard for RAG Faithfulness Evaluation`
- `README_REPRODUCE.md`
- `requirements.txt`
- `requirements-full.txt`
- `Dockerfile`
- `Makefile`
- `run_all_analysis.sh`
- `SOURCE_TRACE.md`
- `CLAIMS_AUDIT.md`
- `artifact_manifest.md`
- `controlledrag_reporting_checklist.md`
- `scripts/` with reviewer-facing verification and optional analysis scripts only
- `src/` with reusable project code
- `experiments/` with experiment entry points and configs needed for optional regeneration
- `data/` with compact/frozen data artifacts required by verification or optional regeneration
- `results/` with final frozen result tables only
- `source_tables/` with compact paper source CSVs
- `human_eval_final/` with final human-evaluation files
- `tests/` smoke tests
- `submission_package/` containing the regenerated anonymous reviewer ZIP

## Result files that will stay and why

- `results/revision/fix_01/`: matched-context audit claim sources
- `results/revision/fix_02/`: scaled audit claim sources
- `results/revision/fix_03/`: scorer-fragility and human-calibration summaries
- `results/revision/context_conditioned_nli/`: context-conditioned NLI rescoring outputs
- `results/revision/fix_04/`: threshold-transfer matrix
- `results/revision/fix_05/`: coherence-vs-noise summaries
- `results/revision/fix_06/`: cost-aware head-to-head summaries
- `results/revision/fix_09/`: confidence-control follow-up retained because it is a completed frozen revision result
- `results/revision/fix_11/`: RAPTOR-2L cost table
- `results/revision/fix_12/`: answer-span/control diagnostic
- `results/revision/fix_13/`: stronger-retriever sanity check
- `results/revision/fix_14/`: second-generator probe summaries
- `results/revision/fix_15/`: long-form stress summaries
- `results/multi_retriever/`: stronger-retriever sanity/source trace support

## Data and human-evaluation files that will stay and why

- `human_eval_final/n99_calibration/`: final n=99 human-evaluation calibration files
- `human_eval_final/n100_disagreement/`: final n=100 targeted disagreement files
- `source_tables/`: compact source CSVs for follow-up diagnostics
- `data/adversarial/`: small frozen adversarial examples used by optional scripts
- `data/benchmark/`: small benchmark metadata
- `data/revision/fix_06/per_query_compact.csv`: compact numeric input for cost-aware CI verification

## Files and folders that will move to the private backup

- Paper source and PDFs: `ragpaper/`, `ragpaper.zip`, `paper_neurips/`, `paper_longform/`, `papers/`, old named paper export folders
- Public demo and release infrastructure: `space/`, `leaderboard/`, `release/`, `pip-package/`, `integrations/`
- Paper-revision and internal docs: `docs/revision/`, `CLAUDE.md`, `AGENTS.md`, `RUNBOOK.md`, `analysis.md`, old submission notes, old revision notes
- Notebook and compute-launch scaffolding that is not reviewer-facing: `notebooks/`, Kaggle launchers, local run-queue helpers, demo/HF/Zenodo upload scripts
- Local stores and caches: `chroma_db/`, generated logs, TeX auxiliary files, operating-system metadata
- Unreferenced or legacy result folders and loose root result CSVs not listed above
- Prior extracted reviewer package contents before regenerating the final ZIP

## Generated junk that may be deleted

- `.DS_Store`
- `._*`
- `__MACOSX/`
- `__pycache__/`
- `.pytest_cache/`
- `.ipynb_checkpoints/`
- TeX auxiliary files: `*.aux`, `*.log`, `*.out`, `*.toc`, `*.fls`, `*.fdb_latexmk`, `*.synctex.gz`

## Anonymity risks to remove

- Author names, personal GitHub links, email addresses, local absolute paths, demo links, paper links, OpenReview/Overleaf/arXiv links, Hugging Face links, and internal assistant notes
- Paper source/PDFs and old submission/revision files
- Scripts whose only purpose is publishing to external personal accounts or public demos

## README content

The README will be rewritten as a concise double-blind artifact overview. It will contain only repository contents, quick-start setup, lightweight verification commands, exact expected human-evaluation values, and notes that generation outputs are frozen and no paid APIs are required for default verification.
