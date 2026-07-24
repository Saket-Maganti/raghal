# Hard-Pinned API Runbook

## Scope

This is an alternative later execution route for the same frozen candidate
and prompt. It was not executed in Prompt 05. Do not combine API and local
judge scores into a fused result.

## Required pins

Before any call, record:

- exact provider;
- exact requested model/version;
- allowed returned model values;
- allowed `X-Routed-Via` value;
- maximum `X-Fallback-Attempts` (default and recommended: zero);
- endpoint version;
- prompt/parser versions; and
- candidate manifest SHA-256.

`provider="auto"`, `model="auto"`, provider fusion, load balancing across
models, and silent fallback are prohibited for a reported experiment.

## Credential handling

Supply the API credential only through the runtime secret manager or a
process environment variable. Do not place it in a notebook, command
history, config, `.env`, result JSONL, checkpoint, ZIP, or repository.
Disable HTTP debug logging and redact authorization headers from exceptions.

## Dry run

Use the mock transport in `CPU_SYNTHETIC_SMOKE_TEST.py`. Confirm:

- the request names the pinned provider/model and sets fusion false;
- the returned model is recorded;
- `X-Routed-Via` and `X-Fallback-Attempts` are recorded;
- unexpected model/provider/fallback values are rejected; and
- raw plus strictly parsed outputs are logged.

This dry run sends no request.

## Later real execution

1. Freeze the candidate and config.
2. Instantiate `FreeLLMAPIAdapter` with `allow_network=True` only in the
   authorized runtime.
3. Rate-limit globally and use deterministic retry rules for transport errors
   only. Never retry based on a score or condition.
4. Write every attempt to `attempt_log.jsonl`; write exactly one final record
   per `row_id` to `raw_and_parsed_outputs.jsonl`.
5. On any unexpected returned model, route, or fallback count, mark
   `routing_rejected` and stop the run rather than accepting a substitute.
6. Resume only by the frozen `row_id` set and reject duplicates.
7. Run post-run validation and build the allow-listed result ZIP.

The API result remains an optional fixed-output sensitivity and cannot be
described as a new retrieval/generation experiment.
