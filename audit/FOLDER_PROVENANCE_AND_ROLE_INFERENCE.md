# Folder Provenance and Role Inference

Roles are inferred from Git state, names, internal manifests, and file layout. No files were merged to make these inferences.

## `rag-hallucination-detection_main`

- **Inferred role:** worktree containing the submitted/reviewer artifact; the exact anonymous submission is `submission_package/neurips2026_reviewer_artifact_anonymous.zip`.
- **Evidence:** the only nested Git repository; clean `main` at `59e94a5418a296acda1892e9165fd43096292f58`; latest commit subject is `Restore reviewer artifact submission package`; `artifact_manifest.md` names that ZIP. The local worktree also contains ignored paper/build material and an identifying remote, so the whole folder was not the anonymous package.
- **Baseline treatment:** copied without scientific repair, subject to explicit public-repository safety exclusions.

## `cleanup_20260506_final_code_artifact_cleanup`

- **Inferred role:** private pre-cleanup capture and cleanup planning worktree.
- **Evidence:** `CLEANUP_PLAN.md`, `root_before_cleanup/`, and the largest number of scientific files/results. It preserves substantially more experiment state than the submitted artifact.

## `deleted_from_head`

- **Inferred role:** files intentionally removed from a prior repository HEAD but retained for forensic recovery.
- **Evidence:** archive/log-oriented layout and absence of a nested Git root.

## `moved_from_repo`

- **Inferred role:** material moved out of the active repository, including paper/submission packages and a generated Chroma database.
- **Evidence:** `submission_package*`, paper archives, and `chroma_db/` paths.

## Completeness versus reproducibility

- **Most complete scientific state by file/result coverage:** `cleanup_20260506_final_code_artifact_cleanup` (1674 non-Git files; 964 result-classified files).
- **Most reproducible bounded baseline:** `rag-hallucination-detection_main` because it is the clean, documented Git snapshot, though its manifests and checks still require validation.
- Completeness does not imply authority: remnant versions remain separate and conflicts are not resolved here.
