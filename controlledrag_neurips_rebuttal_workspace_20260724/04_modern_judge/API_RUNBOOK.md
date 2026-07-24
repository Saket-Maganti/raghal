# Hard-Pinned API Runbook

## Scope

This is an unexecuted alternative transport for the same frozen candidate and
prompt. Never combine API and local judge scores into a fused result.

## Immutable contract

Freeze candidate/SHA, source SHA, provider, exact provider model version,
allowed returned model, allowed route, zero fallbacks, endpoint version,
prompt v2, parser v2, transport, retry budget, generation settings, label
thresholds, and strict validity gates before the first call. `auto`, fusion,
load balancing across models, mutable aliases, and silent fallback are
prohibited.

Use only `prompt_rendering.render_prompt`. Construct `JudgeRequest` from its
`RenderedPrompt`; `FreeLLMAPIAdapter` sends explicit system/user messages for
`chat_template` or its deterministic flattened form for `plain_text`. Do not
copy prompt text into an API-specific renderer.

## Credentials and dry run

Provide credentials only through the authorized runtime secret manager or
process environment. Never store them in config, notebook, logs, checkpoints,
ZIPs, `.env`, or Git. Disable HTTP debug output and redact authorization
headers from errors.

Run `CPU_SYNTHETIC_SMOKE_TEST.py` first. Its mock transport checks canonical
messages, fusion false, routing headers, returned model, raw output, token
metadata, strict parsing, exception typing, retries, and rejection behavior
without sending a request.

## Later authorized execution

1. Use `execute_row_with_retries`; do not write a provider-specific loop.
2. Append every attempt with unique `(run_id,row_id,attempt)`.
3. Retry only parse/provider failures within the frozen budget. Never retry
   based on condition, score, or apparent correctness.
4. Treat unexpected/missing route, model, or fallback metadata as terminal
   `routing_rejected`; retain available response metadata and quarantine the
   entire run.
5. Resume only eligible rows with unchanged prompt hash, run ID, and retry
   budget. Reject duplicate/conflicting attempts and partial JSONL.
6. Atomically derive exactly one terminal final record per row.
7. Apply the same strict post-run gates and allow-listed ZIP builder as the
   local route.

An API result remains optional fixed-output scorer sensitivity, never fresh
retrieval/generation or universal ground truth.
