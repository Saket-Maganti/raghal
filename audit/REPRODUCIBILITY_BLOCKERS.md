# Reproducibility Blockers

## Observed lightweight-check failures

- `cleanup_20260506_final_code_artifact_cleanup` / `python compileall`: SyntaxError: from __future__ imports must occur at the beginning of the file
- `rag-hallucination-detection_main` / `python compileall`: SyntaxError: from __future__ imports must occur at the beginning of the file
- `moved_from_repo/pip-package` / `pytest collection`: no tests collected, 1 error in 0.13s
- `moved_from_repo/pip-package` / `lightweight pytest`: 1 error in 0.13s

The package tests pass when `PYTHONPATH=src` is supplied, so the direct failure is a fresh-clone/install-path issue rather than a core test failure.

## Concrete source-trace and documentation blockers

- The submitted artifact contains only `data/revision/fix_06/per_query_compact.csv`; full fix-01/fix-02/fix-03 and other per-query inputs are present only in the cleanup pre-cleanup tree.
- `Controlled_RAG___Saket/supplement.tex` references top-level `audit_log.md`, which is absent from the submitted worktree and reviewer ZIP.
- `Controlled_RAG___Saket/checklist.tex` says `run_all_analysis.sh` regenerates every main-paper analysis table, but the script runs only the n=99 and n=100 human-evaluation checks.
- `data/benchmark/README.md` references `scripts/package_benchmark.py`, absent from the submitted artifact.
- `results/revision/fix_09/` was listed for retention in `CLEANUP_PLAN.md` and exists in cleanup snapshots, but is absent from the submitted worktree.
- The Together/Llama-3.3-70B `fix_07` script exists, but no frozen fix-07 inputs or outputs were found in any tree.
- Several legacy scripts reference absent `results/human_eval/` or `results/frontier_scale/` paths.

## Scientific reproducibility blockers not resolved by smoke tests

- Remnant outputs are not yet cryptographically traced to the submitted code/configuration.
- Same-relative-path conflicts across folders remain unadjudicated.
- A complete paper claim/table/figure-to-input-to-command map has not been manually verified.
- External APIs, model versions, datasets, seeds, and hardware-dependent generation were not exercised.
- Absolute local paths in scripts/logs may prevent fresh-clone execution.
- Requirements are not a fully locked environment and several declared packages are absent from the audit environment.
