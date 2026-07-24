# Prompt 05 Handoff

## Outcome

The optional modern-judge package is complete at build-only status
`PREPARED_NOT_EXECUTED`. It contains four deterministic nested candidates,
strict prompt/parser/schema contracts, hard-pinned local/API adapters,
routing rejection, a guarded T4×2 notebook, checkpoint/resume and duplicate
controls, post-run analysis, deterministic ZIP packaging, and ingestion
gates. Only synthetic/mock tests ran.

## Prompt 6 safe inputs

Prompt 6 may inspect all files in `04_modern_judge/` as prepared tooling. It
must not describe any candidate as scored or imply a modern-judge result
exists. `BUILD_VALIDATION_REPORT.md` records the only executed tests.

## Candidate and primary endpoint

- Candidates: 300/400/500/600 fixed rows.
- Complete baseline–HCPC-v1 pairs: 100/133/167/200.
- Preferred operational choice: freeze 600 before execution if resources
  allow; smaller candidates are prebuilt fallbacks, not outcome-selected
  interim samples.
- Primary endpoint if later executed: paired mean
  `baseline - hcpc_v1` score contrast with a 10,000-resample paired
  percentile bootstrap 95% CI.

## Notebook readiness

The notebook defaults to `RUN_REAL_INFERENCE = False`, runs the CPU synthetic
suite in that state, separately requires the run-config real flag, detects
T4×2, supports one worker per fitting GPU or one multi-GPU device-map worker,
supports 4-bit/8-bit/BF16/FP16 configuration, resumes checkpoints, rejects
duplicate final rows, and retains raw plus parsed output before building an
allow-listed result ZIP.

## Planning-only runtime

For a pinned 7B–8B model on T4×2, the later 600-row run is estimated at
roughly 20–50 minutes in 4-bit, 30–70 minutes in 8-bit, or 40–90 minutes in
FP16 if it fits. Larger 13B–14B 4-bit models are estimated at 40–100 minutes;
multi-GPU or larger-model paths may take 70–300 minutes. These are unmeasured
planning ranges.

## Unresolved choices

The final candidate size, local versus API route, exact provider and
model/revision, allowed routing metadata, quantization/dtype/GPU strategy,
license/access, and current cost/rate limits remain deliberately unset.
`model="auto"` and fusion remain prohibited.

## Scientific boundaries

- The package is optional and the rebuttal remains complete without it.
- Any later run is fixed-output rescoring, not fresh retrieval/generation.
- No modern judge may be called universally correct or ground truth.
- The two human slices must remain separate.
- No stale metric value or quarantined P0 claim may enter later analysis.
- Raw later outputs require privacy and routing review before Git ingestion.

## Git receipt

- Content commit: `92dea85d736cdfdc994a96abb9a6ae7094f9efd3`
- Remote branch: `origin/neurips-rebuttal-validation-20260724`
- Push result: `SUCCESS_REMOTE_VERIFIED`

The remote ref, fetched tracking ref, and GitHub commit API all resolved to
the content commit after the non-force push.
