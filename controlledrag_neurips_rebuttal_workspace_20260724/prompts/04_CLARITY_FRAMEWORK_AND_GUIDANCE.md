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

# Sub-Prompt 4 — Clarity, Framework Rationale, and Practitioner Guidance

## Estimated time

**3–5 hours**

## Dependency

Read:

- `01_provenance/REVIEWER_CONCERN_MATRIX.md`
- `01_provenance/META_REVIEW_RESPONSE_MAP.md`
- `01_provenance/P0_INTEGRITY_GATE.md`
- `03_existing_analyses/PROMPT_03_HANDOFF.md`

## Objective

Transform verified evidence into clear reviewer-facing explanations without yet drafting final responses.

## Required deliverables

Create:

1. `05_clarity_material/EXPERIMENT_EVIDENCE_MATRIX.md`
   - research question;
   - dataset/split;
   - sample size;
   - generator/retriever/context;
   - scorer/input format;
   - seed;
   - output origin;
   - uncertainty method;
   - primary finding;
   - evidence strength;
   - source files.

2. `05_clarity_material/METRIC_DICTIONARY.md`
   - plain definition;
   - implementation definition;
   - input/output;
   - range/direction;
   - aggregation/threshold;
   - package;
   - common misinterpretation;
   - paper location.

3. `05_clarity_material/SEVEN_AXIS_RATIONALE.md`
   - generator;
   - retriever;
   - context structure;
   - scorer;
   - human calibration;
   - threshold transfer;
   - cost.

Required framing:
- practical non-redundant disclosure categories;
- not mathematically unique;
- not formally exhaustive;
- disclose all seven;
- stress-test only claim-critical choices.

4. `05_clarity_material/FIGURE_2_PLAIN_LANGUAGE_EXPLANATION.md`
   - one sentence;
   - one paragraph;
   - caption-length version.

5. `05_clarity_material/SCOPE_AND_GENERALIZATION_STATEMENT.md`
   - separate methodological contribution from scoped numerical findings.

6. `05_clarity_material/CONTROLLEDRAG_DECISION_PROTOCOL.md`
   - stable;
   - conditional;
   - unresolved;
   - operational procedure;
   - Pareto decision rule.

7. `05_clarity_material/REBUTTAL_READY_CLARITY_BLOCKS.md`
   - concise blocks for metrics, scope, sign flip, experiments, seven axes, human evaluation, cost, threshold transfer, and Figure 2.

8. `05_clarity_material/PROMPT_04_COMPLETE.md`
9. `05_clarity_material/PROMPT_04_HANDOFF.md`

## Git completion

Update `GITHUB_HANDOFF_INDEX.md`.

Run privacy/secret scan and inspect staged diff.

Commit message:

```text
rebuttal(p4): add clarity framework and decision guidance
```

Push only when repository privacy is confirmed.

Record commit SHA and push status.

## Final response

Report:

- clarity package status;
- strongest concise framing;
- practitioner protocol status;
- remaining writing risks;
- commit SHA;
- push status;
- Prompt 5 readiness.
