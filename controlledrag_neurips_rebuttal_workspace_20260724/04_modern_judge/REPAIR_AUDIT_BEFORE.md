# Prompt 05 Pre-Repair Audit

Audit baseline: content commit
`92dea85d736cdfdc994a96abb9a6ae7094f9efd3`, receipt commit
`f50f84754cbc59be07df87785914472ae39a944b`.

No real model, API, network judge, model download, Kaggle/Colab job, GPU
inference, or real-row scoring was used for this audit.

## Confirmed critical defects

| Defect | Risk | Affected files |
| --- | --- | --- |
| `max_attempts_per_row` exists but no retry loop exists | Declared protocol and execution diverge | notebook, run config |
| Resume marks every prior result complete, including retryable failures | Failed rows can be silently skipped | notebook |
| Shard result files append multiple records per row and are later treated as final records | Duplicate/conflicting finals and invalid resume state | notebook |
| Every exception becomes `provider_error` | Parse and routing failures lose their scientific meaning | notebook, adapters |
| Routing exceptions discard returned routing metadata in the stored record | Route violations are not fully auditable | provider adapter, notebook |
| Scientific validity ignores parse failures and complete-case shrinkage | A failed, condition-asymmetric run can be called valid | post-run analysis |
| Missing/extra/duplicate rows are raised or omitted rather than fully reported | Failure diagnostics are incomplete | post-run analysis |
| Attempt logs are not checked against final terminal records | Final state cannot be proven from attempt history | post-run analysis |
| Prompt version 1 does not treat embedded instructions as untrusted data | Prompt-injection and delimiter collision risk | prompt, notebook |
| Prompt rendering is duplicated in the notebook | API/local paths can drift from the frozen prompt | notebook, adapters |
| Model emits both label and score | Internally inconsistent outputs are possible | prompt, parser, schema |
| Hugging Face tokenization silently truncates | Different evidence can be judged without disclosure | Hugging Face adapter |
| Hugging Face loading does not distinguish offline snapshot from authorized download | Ambiguous provenance and accidental network risk | Hugging Face adapter, config |
| Quantized loading uses legacy boolean flags | Quantization configuration is incomplete and weakly recorded | Hugging Face adapter |
| T4/BF16 compatibility is not enforced | Requested dtype may be unsuitable or silently altered | notebook, Hugging Face adapter |
| Chat templates are unsupported | Instruct/chat models may receive the wrong transport | adapters, config |
| Generation metadata is incomplete | Reproduction and termination diagnosis are weak | adapters, schema |
| Schema omits pair/condition/version/revision/token/device/terminal fields | Final rows do not carry required provenance | output schema, record builder |
| Checkpoint/final/runtime writes are direct and non-atomic | Crashes can leave corrupted state | notebook, post-run analysis |
| JSONL readers accept blank lines and do not explicitly detect partial tails | A crash-truncated attempt can be overlooked | post-run analysis |
| ZIP allow-list does not require all core scientific files | An incomplete package can be produced | ZIP builder |
| Synthetic tests cover only a small happy path | Retry, crash, validity, injection, and config defects are untested | CPU smoke test |

## Confirmed documentation and bookkeeping defects

- The pre-registration does not freeze retry eligibility, strict zero-error
  defaults, deterministic label thresholds, prompt escaping, source modes,
  prompt transport, or context-length rejection.
- The Kaggle/API runbooks do not describe attempt uniqueness, atomic state,
  strict terminal gates, or canonical prompt rendering.
- The handoff index still says Prompt 06 is blocked merely because the
  repository is public, although package readiness and missing exact reviews
  are separate issues.
- Prompt 05 completion language predates this repair and must not be read as
  approval to execute a real model.

## Repair design decision

Use pre-run-fatal `ConfigurationError` for invalid immutable configuration,
and a terminal per-row `integrity_error` for row-specific context-length or
prompt/input integrity failures. Keep `routing_rejected` terminal and
non-retryable. Only `parse_error` and `provider_error` are retryable, and only
up to the frozen per-row maximum. The default scientific gates require every
manifest row to terminate successfully with zero parse/provider/routing or
integrity errors.
