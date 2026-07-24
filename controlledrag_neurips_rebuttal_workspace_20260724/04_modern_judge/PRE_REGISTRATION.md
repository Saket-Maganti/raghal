# Optional Modern-Judge Pre-Registration

## Status and boundary

This is a prospective plan for optional post-submission fixed-output
rescoring. It is not evidence that the original study was preregistered and
does not create a result. Prompt 05 and its repair performed synthetic/mock
validation only. Status remains `PREPARED_NOT_EXECUTED`.

## Research question and sample

On the fixed 600-row SQuAD/Mistral panel, does a hard-pinned modern
question+context+answer judge reproduce, attenuate, or reverse the
baseline-minus-aggressive-refinement score contrast? Four deterministic,
nested candidates contain 300, 400, 500, and 600 rows. Choose one candidate
before any modern-judge output is seen; smaller candidates are resource
fallbacks, not sequential outcome-based looks.

`SAMPLE_SELECTION.py` verifies the source SHA, ranks complete query groups
with frozen salt `controlledrag-modern-judge-v1`, maximizes paired coverage,
and adds at most two deterministic extras for 400/500. Manifests contain no
raw question, context, answer, prior score, or human label.

## Frozen prompt and output

- Prompt: `controlledrag-modern-judge-prompt-v2`.
- Parser: `strict-score-json-v2`.
- The canonical renderer is `prompt_rendering.py`; notebook and adapters may
  not maintain an ad hoc renderer.
- Question, context, and answer are escaped and placed inside structured
  untrusted-data blocks. Embedded instructions are evidence, never commands.
- The model returns exactly `score` and `reason`. Score is the primary
  continuous endpoint.
- Labels are derived after parsing: unsupported `<0.33`, partially supported
  `0.33–<0.67`, supported `>=0.67`. These are operational descriptive
  thresholds, not universal semantic truth.
- Reasons are limited to 60 whitespace tokens.

## Provider, model, and transport

Before execution freeze provider, exact model ID, immutable revision, one
allowed returned model, route allow-list, zero fallback attempts, quantization,
dtype, generation settings, and `plain_text` or `chat_template` transport.
`auto`, fusion, silent fallback, mutable `main`/`latest`, and mixed models are
prohibited.

For Kaggle, choose exactly one:

1. `offline_snapshot`: uploaded immutable snapshot, non-empty snapshot path,
   `local_files_only=true`; or
2. `huggingface_download`: explicitly authorized internet access,
   `local_files_only=false`, exact model ID and immutable revision.

T4 runs reject BF16 under the frozen compatibility policy; FP16 is preferred.
Quantized runs use an explicit bitsandbytes configuration. Actual parameter
dtype and quantization are recorded and may not silently differ.

## Context and generation

The context policy is `reject_if_too_long`. Before generation, count prompt
tokens and require `prompt_tokens + max_new_tokens` not to exceed the minimum
of the frozen and runtime model limits. Silent truncation is prohibited.
Generation is deterministic: sampling off, temperature zero, top-p one,
top-k zero, frozen seed, fixed maximum new tokens, and recorded EOS/pad IDs,
library versions, CUDA version, token counts, finish reason, and transport.

## Retry and resume policy

The default maximum is two attempts per row.

| Status | Retry | Terminal |
| --- | --- | --- |
| `ok` | No | Yes |
| `parse_error` | Until frozen budget is exhausted | At exhaustion |
| `provider_error` | Until frozen budget is exhausted | At exhaustion |
| `routing_rejected` | Never | Yes; whole run quarantined |
| `integrity_error` | Never | Yes; whole run invalid |
| configuration error | Never | Pre-run fatal |

Retries are never selected by condition, score, or apparent correctness.
Every attempt has the unique key `(run_id,row_id,attempt)` and is append-only.
Resume never reruns successful or other terminal rows. It retries only
eligible parse/provider failures, rejects changed retry budgets or prompt
hashes, and rejects duplicate/conflicting attempts.

## Primary and secondary endpoints

Primary: mean paired `baseline - hcpc_v1` score over complete successful query
pairs, with a 10,000-resample paired percentile bootstrap 95% CI. Secondary:
`hcpc_v2 - hcpc_v1`, `baseline - hcpc_v2`, condition means, derived-label
distributions, retry/error diagnostics, and later bounded scorer correlations.
Human alignment must keep the distinct `n=99` and `n=100` slices separate.

For every contrast report candidate pairs, complete successful pairs,
excluded pairs, exclusion causes, condition asymmetry, and whether the frozen
minimum pair count passes.

## Strict default scientific-validity gates

The default rebuttal-grade configuration freezes:

- maximum parse-error rate `0`;
- maximum provider-error rate `0`;
- maximum condition error-rate difference `0`;
- all manifest rows required terminal;
- all manifest rows required `ok`;
- no routing, integrity, configuration, source, prompt, model, provider,
  manifest, duplicate, extra, missing, or attempt-history inconsistency; and
- the primary complete-pair minimum chosen before outputs.

A later author may relax an error or pair threshold only before seeing
outputs and must retain that changed config. Complete-case estimates may be
diagnostic, but no invalid run receives rebuttal-safe interpretation.

## Persistence and interpretation

Shard attempts are append-only. Checkpoints, consolidated attempt logs, final
terminal JSONL, runtime metadata, and analysis summaries use atomic
temp-file-plus-rename writes. Raw outputs are never rewritten.

Any accepted finding is a bounded scorer sensitivity on fixed
SQuAD/Mistral outputs—not fresh retrieval/generation, broad generalization,
ground truth, or proof of a universally correct judge. The rebuttal remains
complete if this optional run is never executed.
