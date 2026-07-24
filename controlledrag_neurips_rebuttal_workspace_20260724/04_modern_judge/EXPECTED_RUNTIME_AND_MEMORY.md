# Expected Runtime and Memory

These are planning estimates, not measurements. No real model or API was run.
Actual time depends on prompt length, model architecture, quantization,
provider queueing, and Kaggle availability.

## Kaggle T4×2 planning ranges

| Pinned model class | Suggested loading mode | Approximate weight/device memory | Strategy | Estimated 300 rows | Estimated 600 rows |
| --- | --- | --- | --- | ---: | ---: |
| 7B–8B | 4-bit | roughly 5–7 GB plus activations/KV per worker | one worker per T4 | 10–25 min | 20–50 min |
| 7B–8B | 8-bit | roughly 9–11 GB plus activations/KV per worker | one worker per T4 | 15–35 min | 30–70 min |
| 7B–8B | FP16 | roughly 14–16 GB weights plus overhead; may be tight | test one worker/GPU only after memory check | 20–45 min | 40–90 min |
| 13B–14B | 4-bit | roughly 9–12 GB plus overhead | one worker/GPU if verified, otherwise device map | 20–50 min | 40–100 min |
| 13B–14B | 8-bit/FP16 | roughly 16–30 GB plus overhead | multi-GPU device map | 35–90 min | 70–180 min |
| 30B–34B | 4-bit | roughly 19–24 GB plus overhead | multi-GPU device map | 60–150 min | 120–300 min |

T4 has 16 GB per GPU. BF16 capability and efficiency should be detected at
runtime; FP16 is generally the safer T4 choice. Long contexts may exceed
these ranges or cause out-of-memory errors even when weights fit.

## API planning ranges

For 300–600 sequential rows, allow roughly 15–120 minutes depending on
provider rate limits and latency. Parallel requests may reduce wall time but
must not change routing, retry, or model pins. Cost cannot be estimated until
the exact provider/model and current pricing are selected.

## Checkpoint budget

With one final JSON record and one attempt record per row, text logs are
expected to remain in the low tens of MB for 600 rows, depending on raw reason
length and provider metadata. Model caches and weights can be many GB and are
explicitly excluded from the result ZIP and Git.
