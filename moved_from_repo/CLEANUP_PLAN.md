# Cleanup Plan

This plan was written before moving or deleting files. The goal is to keep the
public repository focused on anonymized reproducibility: setup instructions,
verification scripts, frozen result tables, source tables, final human-eval
files, and smoke tests.

## Keep

- `README.md`: public quick-start instructions; rewrite as a concise anonymous
  reproducibility README.
- `README_REPRODUCE.md`: detailed run and verification instructions; remove
  paper links, live demos, revision history, and identifying references.
- `requirements.txt`: minimal verification dependencies.
- `requirements-full.txt`: optional full experiment dependencies.
- `Dockerfile`, `Makefile`: keep only if they remain anonymous and useful for
  reproducibility; remove paper-build targets if they point to removed paper
  trees.
- `run_all_analysis.sh`: keep as the default lightweight verification command.
- `SOURCE_TRACE.md`, `CLAIMS_AUDIT.md`, `artifact_manifest.md`,
  `controlledrag_reporting_checklist.md`: keep if scrubbed of paper-source
  paths, paper PDFs, revision references, and author-identifying details.
- `scripts/`: keep analysis and verification scripts required for the frozen
  results; move demo/release/upload/paper-specific helper scripts if they are
  not needed for review-time verification.
- `src/`: keep reusable project code needed by experiments and tests; move
  optional paid-API wrappers if they are not needed for the anonymized
  verification path and would trigger final artifact leak scans.
- `experiments/`: keep experiment entry points and configs needed to document
  expensive regeneration paths; scrub or move internal revision logs and
  paper-build helpers.
- `data/`, `results/`, `source_tables/`: keep frozen source tables and final
  CSVs used to verify reported claims. Do not alter scientific labels or
  numerical results.
- `human_eval_final/`: keep all final human-evaluation files.
- `tests/`: keep smoke tests that can run without removed paper sources or
  private infrastructure.
- `.github/workflows/ci.yml`: keep only if updated to the cleaned artifact
  structure.
- `submission_package/`: keep only the current anonymous reviewer artifact ZIP;
  regenerate it after cleanup.

## Move To Private Backup

- `papers/`: paper source, PDFs, auxiliary files, and revision plans are out of
  scope for the double-blind code artifact.
- `Controlled_RAG___Saket/`: Overleaf export and compiled paper material.
- `ControlledRAG_Overleaf_Updated.zip`: Overleaf export archive.
- `space/`: live demo / Hugging Face Space files.
- `docs/revision/`: internal revision notes and runbooks.
- `release/`: public release metadata, dataset packaging, citations, and links
  that may identify authors or live demos.
- `pip-package/`: package publishing metadata and stale public links.
- `leaderboard/`: public-facing demo/benchmark app surface.
- `integrations/`: integration demos not required for verification.
- `notebooks/`: old notebook history with personal repository links.
- `chroma_db/`: generated local vector store.
- `submission/`: paper submission metadata and checklist material.
- `submission_packages/`: old duplicate submission-package archive tree.
- `archive/`: old logs, old ZIPs, and revision/session history.
- `artifacts/generated/space_deploy_snapshot/`: generated live-demo snapshot.
- `main.py`: legacy demo/eval entry point if not referenced by verification.
- Root markdown/checklist/history files already removed from the working tree
  should be backed up from `HEAD` when possible before committing their removal.
- API-upload, demo-generation, and paper-package scripts if they are not needed
  by verification and contain identifying links or demo/paper references.
- Optional paid-API source wrappers if they are not needed by the default
  verification path and would trigger final anonymous-artifact leak scans.
- `CLEANUP_PLAN.md` itself before final commit if the public repo should contain
  only runnable artifact material.

## Delete As Generated Junk

- `.DS_Store`, `._*`, and `__MACOSX/`.
- `__pycache__/`, `.pytest_cache/`, and `.ipynb_checkpoints/`.
- LaTeX build outputs: `*.aux`, `*.log`, `*.out`, `*.toc`, `*.fls`,
  `*.fdb_latexmk`, and `*.synctex.gz`.
- Other generated caches created by local verification commands.

## Requires Checking Before Moving

- `scripts/compute_*`: these may be needed to verify paper-claim tables; keep
  unless a script is strictly release/upload/demo/paper infrastructure.
- `experiments/fix_*.py` and `experiments/run_*.py`: expensive regeneration
  code may be useful for reproducibility, but logs and internal notes should
  move out.
- `data/revision/` and `results/revision/`: these names look revision-like, but
  they contain frozen source/results used by verification; keep required CSVs
  and document unavoidable dataset text hits from leak scans.
- `artifacts/`: keep only if a script or claim trace needs it; move generated
  demo snapshots.
- `.github/workflows/ci.yml`: update if kept because it currently references
  paper/package paths that will be removed.
- `Makefile`: update if kept because paper build targets are not part of the
  anonymous code artifact.
- `Dockerfile`: keep if it supports code verification without pointing to
  removed demo/paper infrastructure.

## Leak-Scan Rules

- Remove or anonymize hits in public-facing docs and final artifact contents.
- Move internal/paper/revision/demo files to private backup.
- Leave unavoidable hits inside frozen source data only when changing them would
  alter scientific evidence; document those as dataset-content false positives.
- The final reviewer ZIP must not include author identity, local paths, live
  demo links, paper links/PDFs, or internal assistant/revision notes.
