# GitHub Handoff Index

| Prompt | Status | Completion marker | Handoff | Commit | Push |
| --- | --- | --- | --- | --- | --- |
| 01 — Git preflight, reviews, claims | Complete with documented review-source blocker | `01_provenance/PROMPT_01_COMPLETE.md` | `01_provenance/PROMPT_01_HANDOFF.md` | `8f66c29f24c2d56637a4ce55e6039766ee4f5ca3` | Pushed and remotely verified by Prompt 04 |
| 02 — Provenance and result verification | Complete with quarantined exclusions | `01_provenance/PROMPT_02_COMPLETE.md` | `01_provenance/PROMPT_02_HANDOFF.md` | `86783cde23b7f3b3bbbe6f53806d8d7d05a785d6` | Pushed and remotely verified by Prompt 04 |
| 03 — Human eval and existing analyses | Complete with bounded conditional findings | `03_existing_analyses/PROMPT_03_COMPLETE.md` | `03_existing_analyses/PROMPT_03_HANDOFF.md` | `1b230659c51baf4ad893f029eaaae718e0eff3e5` | Pushed and remotely verified by Prompt 04 |
| 04 — Clarity framework and guidance | Complete | `05_clarity_material/PROMPT_04_COMPLETE.md` | `05_clarity_material/PROMPT_04_HANDOFF.md` | `a10cf8160e569fe73ec68470bbe5295dea4c33aa` | `origin/neurips-rebuttal-validation-20260724`: success; remotely verified |
| 05 — Build-only judge/Kaggle package | Complete; prepared, not executed | `04_modern_judge/PROMPT_05_COMPLETE.md` | `04_modern_judge/PROMPT_05_HANDOFF.md` | `92dea85d736cdfdc994a96abb9a6ae7094f9efd3` | `origin/neurips-rebuttal-validation-20260724`: success; remotely verified |
| 05 repair — Judge hardening and validity gates | `PROMPT_05_REPAIRED_PREPARED_NOT_EXECUTED` | `04_modern_judge/PROMPT_05_REPAIR_COMPLETE.md` | `04_modern_judge/PROMPT_05_REPAIR_HANDOFF.md` | `1205339ba8d856f48c7f1bfa6e256d47ac192a1c` | `origin/neurips-rebuttal-validation-20260724`: content success; remotely verified |
| 06 — Rebuttal red-team/final handoff | Code/package readiness: ready; reviewer-specific drafting blocked until exact reviews are supplied | — | — | — | Not blocked by repository visibility |

The Prompt 01 content commit is recorded without rewriting it. See
`01_provenance/COMMIT_RECEIPT.md`.

The Prompt 04 public-safe push was explicitly authorized by its push
override. The content SHA was verified by remote ref, fetched tracking ref,
and GitHub commit API before this receipt update.

Prompt 05 likewise carried an explicit public-safe push override. Its content
SHA was verified by remote ref, fetched tracking ref, and GitHub commit API
before this receipt update.

## Prompt 05 repair receipt

- Repair content commit: `1205339ba8d856f48c7f1bfa6e256d47ac192a1c`
- Repair verification receipt commit: `THIS_COMMIT` (verified remote HEAD)
- Remote branch: `origin/neurips-rebuttal-validation-20260724`
- Push result: `SUCCESS_REMOTE_CONTENT_VERIFIED`

The repair content SHA was verified by remote ref, fetched tracking ref, and
GitHub commit API before this receipt update.
