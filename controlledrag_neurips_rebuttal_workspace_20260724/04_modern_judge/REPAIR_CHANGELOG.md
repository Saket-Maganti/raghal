# Prompt 05 Repair Changelog

## Execution and state

- Added `judge_execution.py` with the actual per-row attempt loop.
- Added `run_state.py` for attempt keys, retry eligibility, terminal state,
  resume reconstruction, shard/snapshot reconciliation, corruption checks,
  and atomic writes.
- Successful, routing-rejected, integrity-failed, and exhausted rows are
  terminal; only in-budget parse/provider failures resume.
- Routing metadata is retained on rejection and the frozen policy quarantines
  the whole run without selectively retrying.

## Prompt and output

- Upgraded to `controlledrag-modern-judge-prompt-v2`.
- Added canonical `prompt_rendering.py`, escaped untrusted data blocks,
  structured delimiters, deterministic digesting, and plain/chat transports.
- Reduced model output to score/reason; labels are derived at 0.33/0.67.
- Expanded the closed output schema to v2 with row/pair/condition, versions,
  model revision, attempts, route, tokens, timing, device, dtype,
  quantization, transport, terminal state, and generation metadata.

## Model/runtime safety

- Added `run_config.py` with hard-pin, immutable-revision, source-mode,
  threshold, transport, generation, and path validation.
- Split offline immutable snapshot from separately authorized download.
- Added T4 BF16 rejection, explicit `BitsAndBytesConfig`, actual dtype and
  quantization recording, tokenizer chat-template support, safe pad fallback,
  deterministic generation metadata, and no-silent-truncation preflight.
- Kept network and model loading disabled by default.

## Scientific validity

- Rebuilt `POST_RUN_ANALYSIS.py` to report missing/extra/duplicate rows,
  schema/integrity failures, status/retry/exhaustion counts, error rates by
  condition, asymmetry, prompt/source/model/route/manifest consistency,
  terminal-attempt consistency, and pair exclusions for every contrast.
- Strict defaults require every manifest row terminal and `ok`, zero
  parse/provider/routing/integrity errors, zero condition error-rate
  difference, and the frozen primary pair minimum.
- Invalid runs receive no rebuttal-safe interpretation.

## Persistence, packaging, and tests

- Added temp-file-plus-atomic-rename output/checkpoint/metadata/analysis writes.
- Preserved shard attempts append-only and rejected partial JSONL, corrupt
  checkpoints, duplicate/conflicting keys, attempts after terminal state, and
  exceeded budgets.
- Strengthened ZIP creation to require the full allow-list, reject unknown
  top-level files, symlinks, cache/secret files, and exclude scratch content.
- Replaced the minimal smoke test with 58 adversarial synthetic tests covering
  retry, resume, crashes, error typing, scientific gates, prompt injection,
  labels, config, API metadata, notebook defaults, and packaging.

All changes remain build-only. No candidate manifest or real result changed.
