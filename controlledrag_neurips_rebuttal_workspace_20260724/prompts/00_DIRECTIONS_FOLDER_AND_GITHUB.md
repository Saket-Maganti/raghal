# Directions — Where to Place and How to Run This Prompt Pack

## Current local structure

Keep:

```text
raghallucination/
├── cleanup_20260506_final_code_artifact_cleanup/
├── deleted_from_head/
├── moved_from_repo/
├── rag-hallucination-detection_main/
└── raghal_ingest_workspace_20260724/
```

Place this prompt pack temporarily anywhere convenient, preferably:

```text
raghallucination/_neurips_rebuttal_prompts/
```

Open `raghallucination/` in Codex.

## Run sequence

Run one prompt at a time in this order:

1. `01_GIT_PREFLIGHT_REVIEWS_AND_CLAIMS.md`
2. `02_PROVENANCE_AND_RESULT_VERIFICATION.md`
3. `03_HUMAN_EVAL_AND_EXISTING_ANALYSES.md`
4. `04_CLARITY_FRAMEWORK_AND_GUIDANCE.md`
5. `05_BUILD_ONLY_JUDGE_AND_KAGGLE_PACKAGE.md`
6. `06_REBUTTAL_REDTEAM_FINAL_GITHUB_HANDOFF.md`

Use a fresh Codex conversation for each prompt while keeping the same folder open.

## What Codex will create

Inside the Git worktree:

```text
raghal_ingest_workspace_20260724/
└── controlledrag_neurips_rebuttal_workspace_20260724/
```

All generated reports, scripts, notebooks, response drafts, and handoffs will be committed there.

## Important privacy requirement

The remote repository must be private before any rebuttal branch is pushed. The prompts deliberately stop remote pushing when privacy is public or unverified.

A public repository can expose confidential review material, author identity, and rebuttal strategy. Do not bypass this guard.

## After each prompt

Check that Codex reports:

- completion marker created;
- commit SHA;
- privacy status;
- push status;
- next-prompt readiness.

Do not proceed when the prior completion gate failed unless the next prompt explicitly supports restricted continuation.

## Final remote branch

Expected branch:

```text
neurips-rebuttal-validation-20260724
```

Do not merge it into `main` during rebuttal preparation.
