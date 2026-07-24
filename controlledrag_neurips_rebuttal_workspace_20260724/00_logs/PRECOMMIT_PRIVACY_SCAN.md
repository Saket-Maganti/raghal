# Pre-Commit Privacy and Secret Scan

Scope:

`controlledrag_neurips_rebuttal_workspace_20260724/`

## Checks

| Check | Result |
| --- | --- |
| Personal absolute-path prefix | 0 matches |
| Local username / author-name marker used by source path | 0 matches |
| Email-address pattern | 0 matches |
| AWS access-key formats | 0 matches |
| GitHub token formats | 0 matches |
| OpenAI-style secret-key format | 0 matches |
| Slack token formats | 0 matches |
| PEM private-key headers | 0 matches |
| `.env`, credential, token, PEM, or key filenames | 0 files |
| Files larger than 5 MB | 0 files |
| Symlinks | 0 |
| External rater name or identity | 0; only author-confirmed generic role wording in copied prompts |
| Verbatim review text | 0; exact reviews were not available |

The original paper-source directory includes an identifying name. Inventory
paths for that directory were replaced with the sanitized label
`SUBMITTED_LOCAL_PAPER`.

The remote owner and personal filesystem prefix are redacted from committed
logs. The public/private visibility result and repository basename remain
recorded without the owner identity.

Outcome: `PASS_FOR_LOCAL_COMMIT`

Push remains prohibited: `PUSH_BLOCKED_REPOSITORY_PUBLIC`.

## Prompt 02 rescan

Prompt 02 repeated the scan after generating the upgraded ledger, independent
result JSON, verifier, integrity reports, completion marker, and handoff.

| Check | Result |
| --- | --- |
| Personal absolute path or local username | 0 matches |
| Email-address pattern in new/modified non-prompt files | 0 matches |
| Common API-key/token/private-key patterns | 0 matches |
| Credential, `.env`, token, PEM, or key filenames | 0 files |
| Files larger than 5 MB | 0 files |
| Symlinks | 0 |
| Cache directories | 0 |
| External rater identity | 0; roles remain generic |
| Files staged outside the rebuttal workspace | 0 |

Prompt 02 outcome: `PASS_FOR_LOCAL_COMMIT`.

## Prompt 03 rescan

Prompt 03 repeated the scan after generating the human-evaluation reports,
analysis script, fixed-output results, safe-number tables, metric audit,
completion marker, and handoff.

| Check | Result |
| --- | --- |
| Personal absolute path or local username | 0 matches |
| Email-address pattern in new/modified files | 0 matches |
| Common API-key/token/private-key patterns | 0 matches |
| Credential, `.env`, token, PEM, or key filenames | 0 files |
| Files larger than 5 MB | 0 files |
| Symlinks | 0 |
| Cache directories | 0 |
| External rater identity | 0; only generic confirmed roles are recorded |
| CSV structure | 14 tables parsed; all rows match header width |
| Required Prompt 03 files | 14 of 14 present |
| Files staged outside the rebuttal workspace | 0 |

Prompt 03 outcome: `PASS_FOR_LOCAL_COMMIT`.

## Prompt 04 rescan

Prompt 04 repeated the public-safe scan after generating the clarity package,
decision protocol, pre-existing branch-push record, completion marker, and
handoff.

| Check | Result |
| --- | --- |
| Personal absolute path or local username | 0 matches |
| Email-address pattern in new/modified files | 0 matches |
| Common API-key/token/private-key patterns | 0 matches |
| Credential, `.env`, token, PEM, or key filenames | 0 files |
| Files larger than 5 MB | 0 files |
| Symlinks | 0 |
| Cache directories | 0 |
| External rater identity | 0; only the generic confirmed role is recorded |
| Verbatim confidential review text | 0; exact reviews remain unavailable |
| Required Prompt 04 files | 9 of 9 present and non-empty |
| Files staged outside the rebuttal workspace | 0 |

Prompt 04 outcome: `PASS_FOR_PUBLIC_SAFE_COMMIT_AND_PUSH`.
