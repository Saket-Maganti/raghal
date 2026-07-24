# GitHub Handoff Index

| Prompt | Status | Completion marker | Handoff | Commit | Push |
| --- | --- | --- | --- | --- | --- |
| 01 — Git preflight, reviews, claims | Complete with documented review-source blocker | `01_provenance/PROMPT_01_COMPLETE.md` | `01_provenance/PROMPT_01_HANDOFF.md` | `8f66c29f24c2d56637a4ce55e6039766ee4f5ca3` | Pushed and remotely verified by Prompt 04 |
| 02 — Provenance and result verification | Complete with quarantined exclusions | `01_provenance/PROMPT_02_COMPLETE.md` | `01_provenance/PROMPT_02_HANDOFF.md` | `86783cde23b7f3b3bbbe6f53806d8d7d05a785d6` | Pushed and remotely verified by Prompt 04 |
| 03 — Human eval and existing analyses | Complete with bounded conditional findings | `03_existing_analyses/PROMPT_03_COMPLETE.md` | `03_existing_analyses/PROMPT_03_HANDOFF.md` | `1b230659c51baf4ad893f029eaaae718e0eff3e5` | Pushed and remotely verified by Prompt 04 |
| 04 — Clarity framework and guidance | Complete | `05_clarity_material/PROMPT_04_COMPLETE.md` | `05_clarity_material/PROMPT_04_HANDOFF.md` | `a10cf8160e569fe73ec68470bbe5295dea4c33aa` | `origin/neurips-rebuttal-validation-20260724`: success; remotely verified |
| 05 — Build-only judge/Kaggle package | Prepared, not executed; Git receipt pending | `04_modern_judge/PROMPT_05_COMPLETE.md` | `04_modern_judge/PROMPT_05_HANDOFF.md` | `PENDING` | `PENDING` |
| 06 — Rebuttal red-team/final handoff | Not started | — | — | — | Blocked while public |

The Prompt 01 content commit is recorded without rewriting it. See
`01_provenance/COMMIT_RECEIPT.md`.

The Prompt 04 public-safe push was explicitly authorized by its push
override. The content SHA was verified by remote ref, fetched tracking ref,
and GitHub commit API before this receipt update.

Prompt 05 likewise carries an explicit public-safe push override. Its final
content SHA and remote result will be added after the scoped commit is pushed
and verified.
