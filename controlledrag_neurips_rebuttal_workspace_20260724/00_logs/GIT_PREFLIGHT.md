# Git Preflight

Recorded: 2026-07-24T05:51:17Z

## Expected layout

All five expected top-level folders were found:

- `cleanup_20260506_final_code_artifact_cleanup/`
- `deleted_from_head/`
- `moved_from_repo/`
- `rag-hallucination-detection_main/`
- `raghal_ingest_workspace_20260724/`

## Worktree resolution

The diagrammed ingest directory itself is not a Git worktree. The actual Git
root is nested at `raghal_ingest_workspace_20260724/raghal/`. This nested
directory is a valid Git worktree and is the repository root used for all
Prompt 01 outputs.

## Repository state before Prompt 01 writes

- Repository root: `WORKTREE_ROOT` (sanitized label for the nested Git root)
- Remote: `https://github.com/<redacted-owner>/raghal.git`
- Repository: `<redacted-owner>/raghal`
- Visibility: `PUBLIC`, verified with authenticated GitHub CLI metadata
- Initial branch: `main`
- Initial HEAD: `aef24a10fd71a0029d7958726ef5eaf3214f47bd`
- Initial tracking state: `main...origin/main`
- Initial uncommitted changes: none
- Git version: `2.52.0`
- GitHub CLI version: `2.96.0`

The remote owner is redacted in committed material to avoid adding identifying
metadata to a double-blind rebuttal workspace. The local Git configuration
retains the exact remote.

## Branch action

Created and switched to:

`neurips-rebuttal-validation-20260724`

No merge, history rewrite, force push, or modification of `main` was
performed.

## Submitted artifact identity

Read-only inspection of the standalone submitted-artifact Git tree found:

- branch: `main`
- HEAD: `59e94a5418a296acda1892e9165fd43096292f58`
- working tree: clean and tracking `origin/main`

This identity is recorded for provenance only; the submitted tree was not
modified.
