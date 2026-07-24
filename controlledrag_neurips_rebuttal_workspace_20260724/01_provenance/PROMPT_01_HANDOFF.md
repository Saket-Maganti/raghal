# Prompt 01 Handoff

## Repository and privacy

- Worktree: nested Git root labeled `WORKTREE_ROOT`
- Branch: `neurips-rebuttal-validation-20260724`
- Starting HEAD: `aef24a10fd71a0029d7958726ef5eaf3214f47bd`
- Submitted artifact HEAD: `59e94a5418a296acda1892e9165fd43096292f58`
- Target visibility: `PUBLIC`
- Push: `PUSH_BLOCKED_REPOSITORY_PUBLIC`
- Remote branch URL: none

## Review mapping

No exact five-review export or AC/meta-review artifact is available. Do not
fill reviewer IDs, scores, confidence, direct questions, positive comments,
or per-review attribution from memory. The current matrices contain 14
sanitized concern clusters without reviewer attribution.

Required input to unblock: a confidential local export or screenshots of all
five reviews and the AC/meta-review. While the repository remains public, use
that material only to create sanitized paraphrases and never commit verbatim
text.

## Claim and evidence state

- Claim ledger: 62 rows, 23 required columns.
- Evidence inventory: 50 hashed files.
- Numerical statuses: `TO_VERIFY`, `SUMMARY_ONLY`, or `SOURCE_MISSING`; none
  are verified.
- Highest-risk conflict: n=100 AUPRC cleanup vs submitted implementation.
- Highest-value missing evidence: recovered full per-query inputs for fix 01,
  02, and 03.
- Submitted artifact contains only one `*per_query*` file.

## Prompt 02 starting order

1. Recompute n=100 metrics from submitted code/data and lock the submitted
   AUPRC convention.
2. Verify n=99/n=100 independence, row identities, label schemas, agreement
   from pre-adjudication labels, and alignment from adjudicated labels.
3. Trace and reconstruct matched-context fix 01.
4. Trace and reconstruct scaled fix 02.
5. Trace and reconstruct scorer-fragility fix 03.
6. Verify context-conditioned NLI as a fixed-generation rescoring subset.
7. Reconcile artifact/source-trace completeness before weaker probes.

Use `HEADLINE_VERIFICATION_QUEUE.md` for the full order.

## Non-negotiable interpretation constraints

- Never use stale cleanup AUPRC values.
- Never pool the `n=99` and `n=100` slices.
- Do not claim context-conditioned NLI is universally correct.
- Do not claim the seven axes are uniquely exhaustive.
- Do not broaden beyond tested settings.
- Describe BGE/E5 evidence as fixed-context re-encoding.
- Describe Qwen2.5 and long-form findings as bounded probes.
- Keep the rebuttal complete without a new modern-judge result.
- Do not execute model/API/Hugging Face/Kaggle/Colab inference.

## Known code/artifact blockers

- Four optional experiment scripts are syntax-broken.
- `audit_log.md` cited by the supplement is absent from the submitted
  artifact.
- The default analysis entry point verifies only the two human-evaluation
  analyses, despite a broader checklist claim.
- Contradictory-context and fix-07/70B results are incomplete or absent.

## Commit and push receipt

The primary content commit is
`8f66c29f24c2d56637a4ce55e6039766ee4f5ca3` and is recorded in
`COMMIT_RECEIPT.md`. No push was attempted because visibility is public.
