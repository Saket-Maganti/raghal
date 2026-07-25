# Prompt B preflight

Date: 25 July 2026.

## Repository identity

| Role | Remote | Start commit | Working branch | Backup refs |
| --- | --- | --- | --- | --- |
| rebuttal workspace | configured rebuttal remote | `fa3e8dd405e0b068fd1502b9075f1d9d7fed60db` | `neurips-rebuttal-prompt-b-20260725` | `backup/main-before-prompt-b-20260725`, `backup/pre-prompt-b-scientific-20260725` |
| source artifact | configured source-artifact remote | `4aca9ae3442454d40effae4354b87e18a3de42c3` | `rebuttal-artifact-cleanup-20260725` | `archive/when-better-retrieval-hurts-pre-controlledrag-cleanup`, `backup/source-main-before-controlledrag-repair-20260725`, `backup/pre-rebuttal-artifact-cleanup-20260725` |

Both worktrees were clean before edits. Both remotes were fetched and updated with fast-forward-only pulls. GitHub CLI authentication was valid. No force push is authorized.

## Canonical paper

- title: *ControlledRAG: A Seven-Axis Minimum Reporting Standard for RAG Faithfulness Claims*
- pages: 25
- SHA-256: `b0264921d9db6f7122f81d413045bcaeed5202f45be89a4f2860d4aa0f15bfad`
- visual audit: all 25 pages rendered and inspected
- public handling: confidential PDF remains outside Git

The source repository contains the ControlledRAG aggregate evidence, but its historical tree mixed older project structure and private row-level material. Pre-cleanup status: `CONFIRMED_SOURCE_REPOSITORY_IDENTITY_DRIFT`.

## Private artifact inventory

Located:

- frozen input directory and ZIP;
- accepted postprocessed output ZIP;
- failed first-run diagnosis;
- accepted left-padding raw shards inside the postprocessed ZIP.

Not located:

- separately named `CONTROLLEDRAG_TARGETED_JUDGE_LEFT_PADDING_FAILED.zip`.

The accepted raw run can be independently validated. Byte identity between two separately packaged ZIPs cannot be established without the missing second archive.

## Safety

Private packages and extracted data are outside Git. Local exclusions protect the expected package names and private recomputation directory.
