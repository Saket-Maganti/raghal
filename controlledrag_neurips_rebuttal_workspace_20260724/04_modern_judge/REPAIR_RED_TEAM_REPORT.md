# Prompt 05 Repair Red-Team Report

## Critical checklist

| Attack/failure mode | Resolution |
| --- | --- |
| Silent complete-case analysis | Strict all-row/all-ok defaults; exclusions and asymmetry reported |
| Retry budget exceeded | Attempt sequence rejects any attempt above frozen maximum |
| Failed row treated complete | Only typed terminal state or exhausted budget is complete |
| Routing collapsed into provider failure | Distinct terminal status with preserved response metadata |
| Routing retried | Explicitly non-retryable |
| Parser failure hidden | Every attempt logged; parse/error rates gate validity |
| Duplicate prompt renderers | Notebook/adapters consume only `prompt_rendering.py` |
| Embedded instruction or closing tag | Untrusted-data system rule and deterministic HTML escaping |
| Score/label disagreement | Model emits no label; deterministic derivation only |
| Mutable model revision | Config rejects common mutable aliases and requires immutable form |
| Ambiguous local/download mode | Exactly one validated source mode |
| T4 dtype reinterpretation | BF16 rejected on T4; actual dtype recorded and checked |
| Implicit quantization | Explicit bitsandbytes configuration and recorded actual mode |
| Missing chat template | Chat transport fails configuration if tokenizer lacks template |
| Silent tokenizer truncation | Tokenize without truncation; reject overlength rows |
| Non-atomic final/checkpoint/metadata | Temp file, fsync, atomic rename |
| Duplicate/conflicting attempt/final | Unique keys, contiguous attempts, snapshot conflict rejection |
| Partial JSONL/corrupt checkpoint | Fatal integrity error |
| Accidental real trigger | Notebook and config both false; both must become true |
| Incomplete/unsafe ZIP | All core files required; unknown, symlink, cache, secret rejected |
| Private path/credential leakage | Public-safe staged scan required before both commits |

## Residual limitations

- No real model has been chosen, licensed, downloaded, loaded, or benchmarked.
- Runtime/memory ranges remain unmeasured planning estimates.
- Model-specific chat templates, context windows, gated access, and
  bitsandbytes compatibility can be confirmed only after the author chooses a
  model; the preflight is designed to fail closed.
- A provider may expose different routing header conventions; the exact
  allowed values must be frozen before an authorized API run.
- Even a fully valid run is a bounded optional scorer sensitivity, not ground
  truth or broad generalization.
- Raw model text may still require privacy/safety review before any public
  ingestion.

No unresolved critical defect was found in the build-only path.

Red-team status: `PASS_BUILD_ONLY_NOT_AN_EXECUTION_AUTHORIZATION`.
