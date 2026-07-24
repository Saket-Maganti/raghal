# Submitted Artifact Baseline

The local folder that contains the submitted-artifact worktree is:

`rag-hallucination-detection_main/`

The strongest evidence identifies the exact submitted anonymous package as:

`rag-hallucination-detection_main/submission_package/neurips2026_reviewer_artifact_anonymous.zip`

The full local folder is a superset: it also contains ignored paper/build material and an identifying nested Git remote that were not in the anonymous ZIP.

Evidence:

- it is the only one of the four source folders with a nested Git repository;
- it is on clean branch `main` at commit `59e94a5418a296acda1892e9165fd43096292f58`;
- the latest commit is titled `Restore reviewer artifact submission package`;
- `artifact_manifest.md` names the reviewer ZIP, and the ZIP contains the documented scripts, source, data, results, human-evaluation files, and tests while excluding the local paper tree.

The publication-safe working tree is preserved without scientific repair. Nested `.git/` internals and personal/private files are not copied; their state or hashes are exported under `audit/`. Every safety exclusion is explicit in `audit/EXCLUDED_FILES_MANIFEST.csv`.
