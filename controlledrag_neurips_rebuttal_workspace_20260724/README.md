# ControlledRAG NeurIPS Rebuttal Workspace

This directory is the sole writable location for the sequential NeurIPS
rebuttal workflow dated 2026-07-24. The submitted artifact and the recovered,
deleted, and moved source trees are evidence sources and must remain unchanged.

## Status after Prompt 01

- Git branch: `neurips-rebuttal-validation-20260724`
- Remote visibility: `PUBLIC`
- Push policy: `PUSH_BLOCKED_REPOSITORY_PUBLIC`
- Review material: no exact five-review export or AC/meta-review artifact was
  found; only a pre-existing sanitized thematic concern matrix was available.
- Numerical claims: inventoried only. No numerical claim is marked verified.
- Modern judge or model runs: none performed.

## Directory roles

- `00_logs/`: Git, environment, command, decision, and blocker records.
- `01_provenance/`: review mapping, claim ledger, evidence inventory, version
  map, verification queue, completion marker, and handoff.
- `02_human_eval/`: reserved for Prompt 03.
- `03_existing_analyses/`: reserved for Prompt 03.
- `04_modern_judge/`: reserved for build-only Prompt 05 material.
- `05_clarity_material/`: reserved for Prompt 04.
- `06_reviewer_responses/`: reserved for Prompt 06.
- `07_final_package/`: reserved for final red-team and packaging.
- `prompts/`: local copy of the complete eight-file prompt pack.

## Scientific guardrails

Keep the `n=99` typical and `n=100` targeted human-evaluation slices separate.
Treat the submitted metric implementation as authoritative for submitted
AUPRC values. Describe re-encoding as re-encoding, not fresh generation.
Bound all claims to tested settings. Do not describe context-conditioned NLI,
one scorer, or the seven axes as universally correct, uniquely exhaustive, or
broadly general.
