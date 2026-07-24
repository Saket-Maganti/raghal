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

# Sub-Prompt 1 — Git Preflight, Review Mapping, and Claim Extraction

## Estimated time

**3–5 hours**

## Objective

Verify the Git worktree and privacy state, create the rebuttal branch and workspace, map the exact reviews/meta-review, inventory evidence, and extract every load-bearing paper claim. Do not yet perform the full numerical verification.

## Step 1 — Git and privacy preflight

From the `raghallucination/` root:

1. Confirm all five expected folders exist.
2. Confirm `raghal_ingest_workspace_20260724/` is a Git worktree.
3. Record:
   - repository root;
   - remote URL;
   - repository owner/name;
   - visibility;
   - current branch;
   - HEAD SHA;
   - uncommitted changes.
4. Do not discard unrelated changes.
5. Create or switch to:
   `neurips-rebuttal-validation-20260724`
6. If the branch already exists, inspect it and continue safely.
7. Never modify or merge `main`.
8. If the repository is public, do not push any rebuttal material. Record:
   `PUSH_BLOCKED_REPOSITORY_PUBLIC`
9. If visibility is unverified, record:
   `PUSH_BLOCKED_PRIVACY_UNVERIFIED`

Create:

- `controlledrag_neurips_rebuttal_workspace_20260724/00_logs/GIT_PREFLIGHT.md`
- `controlledrag_neurips_rebuttal_workspace_20260724/00_logs/PRIVACY_STATUS.md`

## Step 2 — Create workspace

Inside the Git worktree, create:

```text
controlledrag_neurips_rebuttal_workspace_20260724/
├── 00_logs/
├── 01_provenance/
├── 02_human_eval/
├── 03_existing_analyses/
├── 04_modern_judge/
├── 05_clarity_material/
├── 06_reviewer_responses/
├── 07_final_package/
└── prompts/
```

Copy this six-prompt pack into `prompts/` if it is locally available.

Create:

- `README.md`
- `00_logs/SESSION_ENVIRONMENT.md`
- `00_logs/COMMAND_LOG.md`
- `00_logs/DECISION_LOG.md`
- `00_logs/FAILURES_AND_BLOCKERS.md`
- `GITHUB_HANDOFF_INDEX.md`

Record source paths using repository-relative or sanitized labels. Do not commit personal absolute paths.

## Step 3 — Read exact reviews and meta-review

Locate the exact five reviews and AC/meta-review from available files, screenshots, exports, or notes.

Create:

### `01_provenance/REVIEWER_CONCERN_MATRIX.md`

For each reviewer:

- reviewer ID;
- score;
- confidence;
- positive comments;
- weaknesses;
- direct questions;
- factual misunderstandings;
- valid limitations;
- evidence already submitted;
- evidence recoverable from project files;
- clarification-only answer;
- existing-output analysis;
- optional new experiment;
- realistic score movement;
- response priority.

Create:

### `01_provenance/META_REVIEW_RESPONSE_MAP.md`

For each concern:

- exact or faithfully paraphrased concern;
- category;
- strongest evidence;
- whether clarification suffices;
- whether existing-output analysis helps;
- whether optional judge evidence could help;
- overclaiming risk.

If the repository is not confirmed private, do not commit verbatim confidential review text. Use precise sanitized paraphrases.

## Step 4 — Extract load-bearing claims

Extract claims from the submitted paper, supplement, figures, tables, captions, checklist, README, `CLAIMS_AUDIT.md`, `SOURCE_TRACE.md`, and manifests.

Create:

### `01_provenance/CLAIM_TO_EVIDENCE_LEDGER.csv`

Include:

- claim_id;
- paper section;
- table/figure;
- claim text;
- submitted value;
- metric;
- dataset;
- split;
- sample size;
- conditions;
- generator;
- retriever;
- context construction;
- scorer;
- scorer input format;
- threshold;
- seeds;
- claimed evidence;
- claimed script;
- claimed config;
- priority;
- initial status;
- notes.

Initial statuses:

- `TO_VERIFY`
- `SUMMARY_ONLY`
- `SOURCE_MISSING`
- `METHOD_ONLY`
- `NON_NUMERICAL`

Do not mark numerical claims verified yet.

## Step 5 — Inventory evidence

Create:

- `01_provenance/EVIDENCE_FILE_INVENTORY.csv`
- `01_provenance/HISTORICAL_VERSION_MAP.md`
- `01_provenance/HEADLINE_VERIFICATION_QUEUE.md`

Hash candidate files. Identify:

- submitted artifact;
- complete cleanup snapshot;
- historical remnants;
- known AUPRC conflict;
- missing full per-query files;
- syntax-broken optional scripts;
- incomplete experiments.

## Step 6 — Completion, scan, commit, and push

Create:

- `01_provenance/PROMPT_01_COMPLETE.md`
- `01_provenance/PROMPT_01_HANDOFF.md`

Update:

- `GITHUB_HANDOFF_INDEX.md`

Before commit:

1. scan generated files for secrets, personal paths, rater identity, tokens, and credentials;
2. inspect staged diff;
3. stage only `controlledrag_neurips_rebuttal_workspace_20260724/`.

Commit message:

```text
rebuttal(p1): map reviews and extract claims
```

Push branch only when repository privacy is confirmed.

Record:

- commit SHA;
- push status;
- remote branch URL if available;
- privacy status.

## Final response

Report:

- repository/privacy state;
- branch;
- reviews found;
- claims extracted;
- evidence inventory count;
- blockers;
- commit SHA;
- push status;
- Prompt 2 readiness.
