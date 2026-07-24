# ControlledRAG NeurIPS Rebuttal — Sequential Codex Sub-Prompt

## Fixed local layout

Run Codex with the following folder open:

```text
raghallucination/
├── cleanup_20260506_final_code_artifact_cleanup/
├── deleted_from_head/
├── moved_from_repo/
├── rag-hallucination-detection_main/
└── raghal_ingest_workspace_20260724/
```

Interpret these paths as:

- `rag-hallucination-detection_main/` — immutable submitted reviewer artifact.
- `cleanup_20260506_final_code_artifact_cleanup/` — recovered cleanup tree, including the most complete pre-cleanup evidence.
- `deleted_from_head/` and `moved_from_repo/` — historical or removed material that may be stale.
- `raghal_ingest_workspace_20260724/` — the Git worktree used to store rebuttal outputs.

The four source folders are read-only. All generated rebuttal material must go inside:

```text
raghal_ingest_workspace_20260724/
└── controlledrag_neurips_rebuttal_workspace_20260724/
```

Do not create another rebuttal workspace outside the Git worktree.

## Global scientific rules

- This is a NeurIPS rebuttal-only workflow.
- Do not work on EACL.
- Do not alter the submitted artifact or any historical source folder.
- Never fabricate, smooth over, or silently reconcile scientific facts.
- Never mix historical and submitted metric implementations.
- Never use stale AUPRC values.
- Never pool the `n=99` and `n=100` human-evaluation slices.
- Never claim context-conditioned NLI is universally correct.
- Never claim the seven axes are mathematically unique or exhaustive.
- Never claim broad generalization beyond the tested settings.
- Never call a re-encoding experiment a fresh end-to-end generation/retrieval experiment.
- Never deanonymize the authors in rebuttal text.
- Do not execute external model APIs, FreeLLMAPI calls, local LLM inference, Hugging Face real-model inference, Kaggle jobs, Colab jobs, or any other real model run.
- Model-run scripts and notebooks may be built and tested only with synthetic/mock data.
- The rebuttal must remain complete without a new modern-judge result.
- Use high reasoning effort and execute the requested work.

## Author-confirmed human-evaluation facts

The following are author-confirmed:

- Two human raters were used.
- Rater 1 was an author.
- Rater 2 was an external person not involved in the project.
- They labelled independently before reconciliation.
- Disagreements were adjudicated afterward.
- Agreement statistics should use pre-adjudication labels.
- Final scorer-alignment analyses should use adjudicated labels.
- The `n=99` typical slice and `n=100` disagreement-targeted slice are distinct and must remain separate.

Do not add unconfirmed details about compensation, qualifications, IRB status, LLM assistance, or adjudicator identity.

## Git and privacy rules

All rebuttal work must be committed to a dedicated branch in the Git worktree so it can be inspected remotely.

Required branch:

```text
neurips-rebuttal-validation-20260724
```

Before writing or pushing:

1. Confirm `raghal_ingest_workspace_20260724/` is a Git worktree.
2. Record the repository root, remote URL, current branch, and HEAD SHA.
3. Check whether the remote repository is private.
4. Never push rebuttal material to a public repository.
5. If privacy cannot be verified, commit locally but do not push. Mark:
   `PUSH_BLOCKED_PRIVACY_UNVERIFIED`
6. Do not merge into `main`.
7. Do not rewrite or force-push history.
8. Stage only files created inside:
   `controlledrag_neurips_rebuttal_workspace_20260724/`
9. Never commit:
   - API keys or environment files;
   - credentials or tokens;
   - external rater identity;
   - personal absolute paths;
   - local usernames;
   - cache directories;
   - model weights;
   - raw secrets;
   - large transient artifacts;
   - any unredacted private identity data.
10. Exact review text may be stored only if the repository is confirmed private. Otherwise store a sanitized concern matrix without verbatim review text.
11. Before each commit, run a secret/privacy scan and inspect `git diff --cached`.
12. Push only the dedicated branch and only after privacy is confirmed.

If `gh` is available, use a command equivalent to:

```bash
gh repo view --json nameWithOwner,visibility,url
```

If `gh` is unavailable, use another authenticated method. If no reliable method exists, do not push.

At the end of every sub-prompt:

- create a completion marker;
- create a handoff file;
- create/update `GITHUB_HANDOFF_INDEX.md`;
- commit only that sub-prompt’s generated outputs;
- push the dedicated branch when privacy is verified;
- record commit SHA and push status.

---

# Sub-Prompt 5 — Build-Only Modern-Judge and Kaggle T4×2 Package

## Estimated time

**3.5–5.5 hours**

## Dependency

Read:

- `01_provenance/P0_INTEGRITY_GATE.md`
- `03_existing_analyses/PROMPT_03_HANDOFF.md`
- `05_clarity_material/PROMPT_04_HANDOFF.md`

## Objective

Build and synthetically test the optional modern-judge execution package. Do not run real inference, download real model weights, call APIs, or launch Kaggle/Colab jobs.

## Required build

Create deterministic candidate sample manifests for:

- 300 rows;
- 400 rows;
- 500 rows;
- 600 rows.

Create:

- `04_modern_judge/PRE_REGISTRATION.md`
- `04_modern_judge/SAMPLE_SELECTION.py`
- `04_modern_judge/SAMPLE_MANIFEST_CANDIDATES/`
- `04_modern_judge/SAMPLE_SELECTION_REPORT.md`
- `04_modern_judge/PROMPT_TEMPLATE.md`
- `04_modern_judge/OUTPUT_SCHEMA.json`
- `04_modern_judge/RUN_CONFIG_TEMPLATE.json`
- `04_modern_judge/provider_adapter.py`
- `04_modern_judge/freellmapi_adapter.py`
- `04_modern_judge/huggingface_adapter.py`
- `04_modern_judge/KAGGLE_T4X2_MODERN_JUDGE.ipynb`
- `04_modern_judge/CPU_SYNTHETIC_SMOKE_TEST.py`
- `04_modern_judge/POST_RUN_ANALYSIS.py`
- `04_modern_judge/BUILD_RESULT_ZIP.py`
- `04_modern_judge/KAGGLE_RUNBOOK.md`
- `04_modern_judge/API_RUNBOOK.md`
- `04_modern_judge/FREELLMAPI_SCIENTIFIC_SAFETY_RULES.md`
- `04_modern_judge/EXPECTED_RUNTIME_AND_MEMORY.md`
- `04_modern_judge/RESULT_INGESTION_RUNBOOK.md`

Notebook rules:

- default `RUN_REAL_INFERENCE = False`;
- require explicit `True` for real execution;
- T4×2 detection;
- one worker per GPU when model fits;
- multi-GPU device map for larger models;
- 4-bit/8-bit/BF16/FP16 options;
- checkpoint/resume;
- no duplicate rows;
- raw and parsed output logging;
- result ZIP;
- synthetic smoke test only.

Adapter rules:

- hard model/provider pinning;
- no `model="auto"` for reported experiments;
- no fusion;
- record returned model;
- record `X-Routed-Via`;
- record `X-Fallback-Attempts`;
- reject unexpected rerouting.

Test only with mocks/synthetic rows.

Create:

- `04_modern_judge/STATUS.md`
- `04_modern_judge/PROMPT_05_HANDOFF.md`

`STATUS.md` must state:

```text
PREPARED_NOT_EXECUTED
```

## Git completion

Update `GITHUB_HANDOFF_INDEX.md`.

Do not commit large generated mock caches or notebook checkpoints.

Run privacy/secret scan and inspect staged diff.

Commit message:

```text
rebuttal(p5): prepare modern judge and kaggle run package
```

Push only when repository privacy is confirmed.

Record commit SHA and push status.

## Final response

Report:

- package completeness;
- synthetic tests;
- notebook readiness;
- status;
- later estimated runtimes;
- unresolved model/API choices;
- commit SHA;
- push status;
- Prompt 6 readiness.
