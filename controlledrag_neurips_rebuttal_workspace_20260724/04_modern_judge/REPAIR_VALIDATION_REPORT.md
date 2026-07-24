# Prompt 05 Repair Validation Report

## Synthetic test result

| Metric | Result |
| --- | ---: |
| Total tests | 58 |
| Passed | 58 |
| Failed | 0 |
| Skipped | 0 |
| Network calls | 0 |
| Model loads/downloads | 0 |
| Real rows scored | 0 |

## Covered gates

- parse/provider retry then success and exhaustion;
- routing rejection terminal without retry;
- eligible-only resume, successful-row suppression, retry-budget enforcement;
- duplicate/conflicting attempts, partial JSONL, corrupted checkpoint, uneven
  shards, atomic state round trips, and terminal-final derivation;
- parse/routing/provider/integrity/configuration exception typing;
- missing, extra, duplicate, parse, provider, routing, asymmetric, and
  insufficient-pair invalidation plus a fully successful passing fixture;
- candidate/successful/excluded pair diagnostics and causes;
- injected instructions, fake JSON, closing-tag collision, deterministic
  rendering, version-sensitive digests, and unresolved placeholders;
- derived-label boundaries, invalid/non-finite scores, reason limits, and
  rejection of model-supplied labels;
- hard pins, immutable revisions, dtype, quantization, model-source
  combinations, prompt transport, T4/BF16, and model-load guard;
- canonical API messages and missing-route rejection;
- JSON-valid/compilable notebook, both false gates, canonical renderer import,
  absence of ad hoc rendering, and actual default-path execution;
- full ZIP allow-list, scratch exclusion, and secret-file rejection; and
- Draft 2020-12 closed output-schema validation for generated attempts/finals.

## Static/build checks

- all Python modules compile;
- Ruff reports no lint findings;
- mypy reports no issues in the nine repaired runtime modules;
- notebook JSON parses and every code cell compiles;
- `RUN_REAL_INFERENCE = False` and config `run_real_inference=false` remain;
- `STATUS.md` retains `PREPARED_NOT_EXECUTED`;
- candidate manifests and their recorded hashes are unchanged.

Status: `SYNTHETIC_REPAIR_VALIDATION_PASS`.
