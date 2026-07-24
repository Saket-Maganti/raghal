# GitHub Handoff Index

| Prompt | Status | Completion marker | Handoff | Commit | Push |
| --- | --- | --- | --- | --- | --- |
| 01 — Git preflight, reviews, claims | Complete with documented review-source blocker | `01_provenance/PROMPT_01_COMPLETE.md` | `01_provenance/PROMPT_01_HANDOFF.md` | `8f66c29f24c2d56637a4ce55e6039766ee4f5ca3` | Pushed and remotely verified by Prompt 04 |
| 02 — Provenance and result verification | Complete with quarantined exclusions | `01_provenance/PROMPT_02_COMPLETE.md` | `01_provenance/PROMPT_02_HANDOFF.md` | `86783cde23b7f3b3bbbe6f53806d8d7d05a785d6` | Pushed and remotely verified by Prompt 04 |
| 03 — Human eval and existing analyses | Complete with bounded conditional findings | `03_existing_analyses/PROMPT_03_COMPLETE.md` | `03_existing_analyses/PROMPT_03_HANDOFF.md` | `1b230659c51baf4ad893f029eaaae718e0eff3e5` | Pushed and remotely verified by Prompt 04 |
| 04 — Clarity framework and guidance | Complete | `05_clarity_material/PROMPT_04_COMPLETE.md` | `05_clarity_material/PROMPT_04_HANDOFF.md` | `a10cf8160e569fe73ec68470bbe5295dea4c33aa` | `origin/neurips-rebuttal-validation-20260724`: success; remotely verified |
| 05 — Build-only judge/Kaggle package | Complete; prepared, not executed | `04_modern_judge/PROMPT_05_COMPLETE.md` | `04_modern_judge/PROMPT_05_HANDOFF.md` | `92dea85d736cdfdc994a96abb9a6ae7094f9efd3` | `origin/neurips-rebuttal-validation-20260724`: success; remotely verified |
| 05 repair — Judge hardening and validity gates | `PROMPT_05_REPAIRED_PREPARED_NOT_EXECUTED` | `04_modern_judge/PROMPT_05_REPAIR_COMPLETE.md` | `04_modern_judge/PROMPT_05_REPAIR_HANDOFF.md` | `1205339ba8d856f48c7f1bfa6e256d47ac192a1c` | `origin/neurips-rebuttal-validation-20260724`: content success; remotely verified |
| Pre-06 — Exact-review ingestion | Complete; sanitized 5/5 reviews and current/initial AC | `06_reviewer_responses/REVIEW_INGESTION_COMPLETE.md` | `06_reviewer_responses/REVIEW_INGESTION_HANDOFF.md` | `2617863d6af05335cf3c72e16c4e63e68ecb535e` | `origin/neurips-rebuttal-validation-20260724`: success; remotely verified |
| 06 — Rebuttal red-team/final handoff | `READY_FOR_PROFESSOR_REVIEW` | `07_final_package/PROMPT_06_COMPLETE.md` | `07_final_package/PROMPT_06_HANDOFF.md` | `2d7699a0a3cf89375f10be8723b6d68d22a6f260` | `origin/neurips-rebuttal-validation-20260724`: content success; remotely verified |
| Final polish — reviewer/AC package and main integration | `FINAL_POLISH_COMPLETE`; `MAIN_REMOTE_VERIFIED`; `LOCAL_REVIEW_BUNDLE_READY` | `07_final_package/FINAL_POLISH_COMPLETE.md` | `07_final_package/FINAL_POLISH_HANDOFF.md` | `4ed74fd9f4a889a21724b004b2761f829334ac3a` | Integration `688be080b06c8cf02e61c9730934c28866a6a7b6` pushed and verified; receipt `THIS_COMMIT` |
| Prompt A — Targeted modern-judge preparation | `READY_FOR_TARGETED_KAGGLE_EXECUTION`; `MAIN_PANEL_WITH_ONE_VALID_HUMAN_SLICE`; `PREPARED_NOT_EXECUTED` | `07_targeted_judge_prepare/PROMPT_A_COMPLETE.md` | `07_targeted_judge_prepare/PROMPT_A_HANDOFF.md` | `cd1ac9083a081374f4e063a89c7bb382f8123f6c` | Main integration `95853923005e42e43038fd0dc1258b0f46b64a63` pushed and verified; receipt `THIS_COMMIT` |

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

## Prompt 06 handoff

- Repository visibility: `PUBLIC`
- Public-safe dedicated-branch push: explicitly authorized by the latest
  Prompt 6 override
- Branch: `neurips-rebuttal-validation-20260724`
- P0: `PASS_WITH_QUARANTINED_EXCLUSIONS`
- Final rebuttal status: `READY_FOR_PROFESSOR_REVIEW`
- Content commit: `2d7699a0a3cf89375f10be8723b6d68d22a6f260`
- Receipt commit: `THIS_COMMIT`
- Push: `SUCCESS_REMOTE_CONTENT_VERIFIED`
- Remote branch:
  `https://github.com/Saket-Maganti/raghal/tree/neurips-rebuttal-validation-20260724`
- Key inspection path:
  `controlledrag_neurips_rebuttal_workspace_20260724/07_final_package/`
- Pull request: not created while public
- Merge to `main`: not performed

## Final polish and main handoff

- Latest authority: sanitized public-safe integration into `main` is
  explicitly required.
- Temporary local branch:
  `rebuttal-final-polish-main-handoff-20260724`
- Backup refs:
  `backup/main-before-final-rebuttal-polish-20260724` and
  `backup/validation-before-final-rebuttal-polish-20260724`
- Polish content commit:
  `4ed74fd9f4a889a21724b004b2761f829334ac3a`
- Main integration commit:
  `688be080b06c8cf02e61c9730934c28866a6a7b6`
- Main receipt commit: `THIS_COMMIT`
- Remote integration verification:
  `SUCCESS_LOCAL_TRACKING_LSREMOTE_GITHUB_API_MATCH`
- Force push: not used
- Validation branch preserved at
  `1c13ccbec74cf596832b11db1eed72a927e17268`
- Local review bundle:
  `CONTROLLEDRAG_FINAL_REBUTTAL_LOCAL/` and
  `CONTROLLEDRAG_FINAL_REBUTTAL_LOCAL.zip` outside Git
- Repository visibility: `PUBLIC`
- Full merge files outside rebuttal workspace: 0
- Confidential exact-review source on `main`: 0

## Prompt A targeted modern-judge preparation

- Preparation content commit:
  `cd1ac9083a081374f4e063a89c7bb382f8123f6c`
- Main integration commit:
  `95853923005e42e43038fd0dc1258b0f46b64a63`
- Main receipt commit: `THIS_COMMIT`
- Remote integration verification:
  `SUCCESS_LOCAL_TRACKING_LSREMOTE_GITHUB_API_MATCH`
- Force push: not used
- Preparation branch preserved:
  `targeted-modern-judge-prepare-20260724`
- Private input directory and ZIP: outside Git
- Real inference, API judge calls, model-weight downloads, and real rows
  scored: zero
- Scientific support class:
  `MAIN_PANEL_WITH_ONE_VALID_HUMAN_SLICE`
