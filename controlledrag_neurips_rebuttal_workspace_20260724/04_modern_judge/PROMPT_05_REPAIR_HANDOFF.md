# Prompt 05 Repair Handoff

## Outcome

`PROMPT_05_REPAIRED_PREPARED_NOT_EXECUTED`.

The optional package now fails closed on configuration, prompt/input
integrity, routing, retry/resume state, schema, source/model provenance,
complete rows, condition-asymmetric errors, and primary pair coverage. All 58
synthetic/adversarial tests pass. No real execution occurred.

## Prompt 6 readiness

Prompt 6 code/package readiness is ready. Reviewer-specific drafting remains
blocked until exact reviews are supplied. Prompt 6 must not imply a modern
judge result exists and should use only the bounded, verified pre-existing
evidence unless a later separately authorized run passes every ingestion gate.

## Later author choices

Before any real run, freeze:

- one candidate and primary complete-pair minimum;
- local Hugging Face versus separately implemented hard-pinned API route;
- exact provider/model/immutable revision and routing allow-list;
- offline immutable snapshot versus authorized download;
- plain text versus tokenizer chat template;
- dtype, quantization, GPU strategy, context window, and token limit;
- license/access, budget, current prices, and rate limits; and
- whether the optional result is needed at all.

## Mandatory boundaries

- Run both false-gated synthetic paths first.
- Never change prompt, parser, sample, retry, label, or validity thresholds
  after seeing outputs.
- Never retry routing/integrity failures or select retries by condition/score.
- Never use an invalid/partial run for rebuttal interpretation.
- Never pool the `n=99` and `n=100` human slices.
- Never call fixed-output rescoring fresh retrieval/generation or ground truth.
- Never commit raw outputs without routing, privacy, and scientific review.

## Git receipt

- Repair content commit: `1205339ba8d856f48c7f1bfa6e256d47ac192a1c`
- Repair receipt commit: `THIS_COMMIT` (verified remote HEAD)
- Remote branch: `origin/neurips-rebuttal-validation-20260724`
- Push result: `SUCCESS_REMOTE_CONTENT_VERIFIED`

The content SHA was resolved through the remote branch ref, fetched tracking
ref, and GitHub commit API before this receipt was written.
