# Privacy Status

Status: `PUBLIC_SAFE_MAIN_PUSH_EXPLICITLY_AUTHORIZED`

Authenticated GitHub metadata reports the target repository visibility as
`PUBLIC`. The latest authoritative final-polish instruction explicitly
requires a non-force integration and push of the sanitized rebuttal package to
`main`. This supersedes earlier validation-branch-only and no-main
instructions.

The authorization does not relax content safety:

- exact confidential review prose and screenshots remain excluded;
- only sanitized concern mappings, public-safe responses, validation reports,
  and handoff metadata may be committed;
- external-rater identity, private contacts, credentials, tokens, environment
  files, personal absolute paths, local usernames, model weights, caches,
  checkpoints, and transient outputs remain prohibited;
- full-workspace, staged-diff, and confidential-source-overlap scans are
  required before commits and pushes;
- the validation branch must remain intact;
- force push and history rewriting remain prohibited; and
- unrelated files and the immutable submitted artifact must not change.

The local review directory and ZIP live outside the Git repository and are
not tracked.

Final-polish privacy result:
`PASS_FOR_PUBLIC_SAFE_SANITIZED_MAIN_COMMIT_AND_PUSH`.
