# RAG Hallucination Project — Preserved Forensic Snapshot

This repository preserves four distinct local project remnants for collaborator inspection before any scientific repair, rerun, or rewrite.

## Source folders

- `rag-hallucination-detection_main/` — the worktree containing the NeurIPS anonymous/reviewer artifact. The exact submitted package is `submission_package/neurips2026_reviewer_artifact_anonymous.zip`; the local folder is a superset.
- `cleanup_20260506_final_code_artifact_cleanup/` — cleanup-era material, including a pre-cleanup tree with broader experiment state.
- `deleted_from_head/` — material recovered or retained after deletion from a prior HEAD.
- `moved_from_repo/` — material moved out of the prior repository, including submission/paper packages and external/generated state.

Folder roles are evidence-based inferences documented in `audit/FOLDER_PROVENANCE_AND_ROLE_INFERENCE.md`. A larger or newer remnant is not automatically more scientifically authoritative.

## Navigate the audit

- Start with `audit/GITHUB_INGEST_REPORT.md`, `audit/FOLDER_PROVENANCE_AND_ROLE_INFERENCE.md`, and `audit/NEXT_ACTION_PLAN.md`.
- File-level hashes, classifications, exclusions, duplicates, and conflicts are in the CSV manifests under `audit/`.
- Technical checks and reproducibility blockers are in `audit/TECHNICAL_HEALTH_REPORT.md` and `audit/REPRODUCIBILITY_BLOCKERS.md`.
- Reviewer-readiness evidence is mapped in `audit/REVIEW_AND_META_REVIEW_CONCERN_MATRIX.md`.

## Preservation and exclusions

No cross-folder scientific merge has occurred. Because this repository is public, nested `.git/` directories, caches, credentials, owner-identifying/private material, and unsuitable large/generated assets are excluded from the copied working trees. Every exclusion is retained by source folder, relative path, byte size, SHA-256, and reason in `audit/EXCLUDED_FILES_MANIFEST.csv`; large/external assets are also listed in `audit/LARGE_OR_EXTERNAL_ASSETS_MANIFEST.csv`.

The source manifest `SOURCE_SNAPSHOT_MANIFEST.sha256` covers the included files in all four preserved trees.

## Next step

Externally inspect this snapshot, then validate claim-to-table-to-result-to-command provenance before selecting any remnant analysis for the NeurIPS rebuttal or any broader experiment for an EACL revision.
