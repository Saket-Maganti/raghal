# FreeLLMAPI Scientific Safety Rules

1. Hard-pin one provider and one exact immutable model version. Never use
   `auto`, fusion, blended providers, load balancing, or silent fallback.
2. Use only canonical prompt v2 rendering. Treat escaped data blocks as
   untrusted evidence, not instructions.
3. Require and retain returned model, `X-Routed-Via`, and
   `X-Fallback-Attempts` for every response.
4. Missing, malformed, unexpected, or over-limit routing metadata is terminal
   `routing_rejected`, never retryable, and invalidates/quarantines the run.
5. Freeze sample, prompt, parser, transport, generation, retry, label, and
   scientific-validity thresholds before outputs.
6. Retry only `parse_error` or `provider_error`, uniformly and only within the
   frozen budget. Never retry by score, label, condition, or correctness.
7. Model output contains only score/reason. Derive the descriptive label at
   thresholds 0.33/0.67.
8. Preserve exact raw output, parser error, attempt number, token counts,
   finish reason, latency, and safe generation metadata.
9. Use unique `(run_id,row_id,attempt)` keys; reject duplicates, conflicts,
   partial JSONL, attempts after terminal state, and budget overruns.
10. Require all rows terminal and `ok` under the strict default gate. Never
    hide complete-case shrinkage or condition-asymmetric failure.
11. Never package credentials, headers, identity data, confidential reviews,
    personal paths, caches, weights, or scratch files.
12. Keep the `n=99` and `n=100` human slices separate.
13. Describe a valid result only as bounded fixed-output sensitivity. The
    rebuttal remains complete if the run fails or never occurs.
