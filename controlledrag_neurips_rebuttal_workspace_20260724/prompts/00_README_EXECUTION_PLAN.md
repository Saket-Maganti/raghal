# ControlledRAG NeurIPS Rebuttal — GitHub-Backed Sequential Prompt Pack

## Folder to open in Codex

Open:

```text
raghallucination/
```

The expected structure is:

```text
raghallucination/
├── cleanup_20260506_final_code_artifact_cleanup/
├── deleted_from_head/
├── moved_from_repo/
├── rag-hallucination-detection_main/
└── raghal_ingest_workspace_20260724/
```

The first four folders are read-only scientific inputs. The fifth folder is the Git worktree where all rebuttal outputs will be created and committed.

## Output location

All prompts must write to:

```text
raghallucination/
└── raghal_ingest_workspace_20260724/
    └── controlledrag_neurips_rebuttal_workspace_20260724/
```

Do not place new rebuttal files beside the five existing folders.

## Git strategy

- Work on branch: `neurips-rebuttal-validation-20260724`
- Never merge to `main`.
- Commit after every prompt.
- Push only if the remote repository is confirmed private.
- If privacy cannot be verified, keep local commits and report `PUSH_BLOCKED_PRIVACY_UNVERIFIED`.
- At the end, create a draft PR only when the repository is confirmed private.
- The final branch should contain reports, scripts, notebooks, handoffs, and rebuttal drafts.
- It should not contain model outputs because no real model/API/GPU inference is being run.

## Run order and estimated time

| Order | Prompt | Responsibility | Estimated time |
|---:|---|---|---:|
| 1 | `01_GIT_PREFLIGHT_REVIEWS_AND_CLAIMS.md` | Git/privacy preflight, workspace, exact review map, claim extraction | **3–5 h** |
| 2 | `02_PROVENANCE_AND_RESULT_VERIFICATION.md` | Full claim tracing, headline verification, AUPRC lock | **4–6 h** |
| 3 | `03_HUMAN_EVAL_AND_EXISTING_ANALYSES.md` | Two-rater verification, metric audit, bootstrap and cost analyses | **3.5–5.5 h** |
| 4 | `04_CLARITY_FRAMEWORK_AND_GUIDANCE.md` | Experiment map, metric dictionary, seven-axis rationale, decision protocol | **3–5 h** |
| 5 | `05_BUILD_ONLY_JUDGE_AND_KAGGLE_PACKAGE.md` | Build-only judge harness, adapters, T4×2 notebook, synthetic tests | **3.5–5.5 h** |
| 6 | `06_REBUTTAL_REDTEAM_FINAL_GITHUB_HANDOFF.md` | Reviewer replies, AC synthesis, red-team, final package, final push/PR | **4–6 h** |

## Total estimated time

| Scenario | Estimated total |
|---|---:|
| Clean provenance and minimal dependency repair | **21–25 h** |
| Realistic | **24–31 h** |
| Multiple mismatches or broken historical tooling | **31–38 h** |

These estimates exclude any real API, local-LLM, Kaggle, Colab, or hosted-model inference.

## Why prompts must remain sequential

Prompts 2–6 depend on verified outputs from the previous prompt. Do not run them simultaneously. A fresh Codex conversation for each prompt is recommended, with the same `raghallucination/` folder open.

## Required Git commits

Suggested commit messages:

1. `rebuttal(p1): map reviews and extract claims`
2. `rebuttal(p2): verify provenance and lock headline results`
3. `rebuttal(p3): validate human evaluation and existing analyses`
4. `rebuttal(p4): add clarity framework and decision guidance`
5. `rebuttal(p5): prepare modern judge and kaggle run package`
6. `rebuttal(p6): finalize reviewer responses and rebuttal handoff`

## Remote access note

The branch must be pushed to a private repository for later inspection through the connected GitHub account. A local commit alone is not remotely accessible. Do not make the repository public for this purpose.
