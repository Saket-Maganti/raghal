# Privacy Status

Status: `PUBLIC_SAFE_PUSH_EXPLICITLY_AUTHORIZED`

Authenticated GitHub metadata reports the target repository visibility as
`PUBLIC`. The latest authoritative Prompt 6 override explicitly authorizes a
non-force push of sanitized rebuttal material to the dedicated branch despite
public visibility. This supersedes earlier visibility-only push blocks.

The authorization does not relax content safety:

- exact confidential review prose and screenshots remain excluded;
- only sanitized concern paraphrases and public-safe response text may be
  committed;
- the external rater’s identity, private contacts, credentials, tokens,
  environment files, personal absolute paths, local usernames, model weights,
  caches, checkpoints, and transient outputs remain prohibited;
- staged and full-workspace privacy/secret scans are required before every
  commit and push;
- only `neurips-rebuttal-validation-20260724` may be pushed;
- force-push and merge to `main` remain prohibited; and
- no pull request is created while the repository is public.

Prompt 6 scan and push results are recorded in
`07_final_package/PROMPT_06_COMPLETE.md`,
`07_final_package/GITHUB_REMOTE_HANDOFF.md`, and
`GITHUB_HANDOFF_INDEX.md`.
