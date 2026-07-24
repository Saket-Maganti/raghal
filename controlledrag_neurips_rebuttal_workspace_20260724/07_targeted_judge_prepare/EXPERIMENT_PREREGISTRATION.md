
# Targeted modern-judge experiment preregistration

Status: `FROZEN_BEFORE_REAL_INFERENCE`

No real model inference, real judge output, or result-direction inspection
occurred while this document was written.

## Scope and frozen rows

The experiment uses one immutable judge and two interfaces on fixed existing
outputs. The main manifest contains 600 eligible fixed rows. The primary
baseline-versus-HCPC-v1 contrast is restricted to the 194 pair IDs complete
under both historical context-conditioned backbones; no missing pair is
imputed. The typical calibration panel uses the 83 adjudicated determinate
binary rows (`supported=1`, `unsupported=0`); the 16
`partially_supported` rows are excluded because no approved binary mapping
exists. The deduplicated disagreement-targeted panel has 72 eligible rows and
is diagnostic because it is below the preregistered minimum of 80. The two
human slices are never pooled.

## Judge and interfaces

Judge: `Qwen/Qwen2.5-7B-Instruct` at immutable revision
`a09a35458c702b33eeacc393d103063234e8bc28`.
Quantization is bitsandbytes NF4 4-bit, float16 compute, double quantization.
Greedy decoding is fixed at `do_sample=false`, `temperature=0`, `top_p=1`,
`max_new_tokens=96`, and `use_cache=true`.

Interface A receives question and answer only. Interface B receives question,
retrieved context, and answer. Role, definition, decision rule, field order,
and strict JSON output schema are identical. The score is the continuous
primary judge output; the boolean is secondary.

## Primary analysis A: fixed-output system contrast

For each interface report the baseline mean, HCPC-v1 mean, and paired mean
contrast `baseline - HCPC-v1` on the 194 locked pair IDs with a 95% paired
bootstrap interval. Report
`context-conditioned contrast - answer-only contrast`.

Classification is frozen as:

- sign reversal: the two point-estimate contrasts have opposite non-zero signs;
- same sign / material magnitude change: same sign and absolute
  difference-in-contrasts is at least 5 score points;
- same sign / small change: same sign and absolute difference is below 5;
- indeterminate: a required point estimate is unavailable or a contrast is
  exactly zero.

The material threshold is fixed at 5 points on the 0–100 scale.

## Primary analysis B: same-row human calibration

Analyze each human slice separately for each interface. Report Spearman
correlation between judge score and human label, sklearn average precision
with faithful=1, and valid-output rate. Compare interfaces with a paired-row
bootstrap for AP and Spearman differences and 95% intervals. The 83-row
typical determinate panel is the sole robustness-qualified bridge. The
72-row disagreement-targeted panel is diagnostic and must not be described as
a robust rebuttal bridge.

## Secondary analysis

For each interface and human slice report boolean accuracy, balanced accuracy,
precision, recall, F1, confusion matrix, and Brier score using
`faithfulness_score / 100`. Secondary metrics cannot displace the primary
outcomes.

## Bootstrap and missingness

Use 10,000 percentile bootstrap replicates with seed 20260724. Resample
complete pair IDs for system contrasts and rows within a human slice for
calibration. Preserve and report requested rows, valid rows, invalid JSON,
schema violations, truncated outputs, OOM/retry failures, duplicate outputs,
and missing outputs. No silent dropping is permitted.

## Context and execution

Maximum input length is 4096 tokens. Preserve question and answer. If needed,
truncate retrieved context from the right only, before first real inference,
record original/final token counts, and apply the same rule deterministically.
No frozen human row is expected to require truncation: a conservative
pre-tokenizer bound of one token per three Unicode characters yields a maximum
under 1,100 tokens across candidate inputs. Exact token counts are checked with
the locked tokenizer before model loading.

Use two independent one-GPU 4-bit replicas under
`torchrun --standalone --nproc_per_node=2`; never use model parallelism or
`device_map="auto"`. Initial and frozen per-device batch size is 4. A
synthetic allocation probe may reduce it only before the first real row is
scored and must record the final value. No precision fallback is allowed.

## Inclusion gates

Strong inclusion requires verified model identity/revision, matching manifest
checksums, at least 98% valid outputs, no differential missingness above 2
percentage points across systems/interfaces, complete primary analysis, no
post-hoc model/prompt selection, and bounded wording.

Valid-output rate from 95% to below 98%, or minor non-differential missingness,
is a qualified inclusion candidate requiring explicit caveats and professor
approval. Exclude if revision is unverified, valid-output rate is below 95%,
differential missingness may alter conclusions, provenance fails, prompts
changed after results, identities differ across shards, outputs are duplicate
or corrupt, or the bundle is not reproducible.

Null, same-direction, opposite-direction, and contrary results are not
exclusion reasons.
