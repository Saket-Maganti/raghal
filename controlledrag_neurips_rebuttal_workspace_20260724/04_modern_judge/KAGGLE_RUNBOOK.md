# Kaggle T4×2 Runbook

## Current state

`PREPARED_NOT_EXECUTED`. No real model, download, API, GPU, Kaggle, or Colab
run occurred during Prompt 05 or its repair.

## Freeze before opening Kaggle

1. Choose one 300/400/500/600 candidate before viewing outputs.
2. Copy `RUN_CONFIG_TEMPLATE.json` to untracked `run_config.json`.
3. Replace every `PIN_`/`SET_` value. Pin one model ID and immutable revision;
   `main`, `latest`, `auto`, fusion, and fallback are prohibited.
4. Record the matching committed candidate SHA and primary pair minimum.
5. Choose `plain_text` or `chat_template`; prompt v2 always comes from
   `prompt_rendering.py`.
6. Keep both real-run gates false for the synthetic pass.

## Choose exactly one model source

### Offline immutable snapshot

- `model_source_mode=offline_snapshot`
- `local_files_only=true`
- `model_snapshot_path` points to the uploaded immutable snapshot directory
- Kaggle internet remains disabled

### Separately authorized Hugging Face download

- `model_source_mode=huggingface_download`
- `local_files_only=false`
- snapshot path is empty
- Kaggle internet is enabled only for the pinned model ID/revision

The config validator rejects ambiguous combinations. Never place a model
cache or snapshot in Git or the result ZIP.

## T4×2 and loading

- The notebook requires exactly two detected T4 GPUs.
- T4 BF16 is rejected; freeze FP16 or FP32. FP16 is the preferred native
  choice.
- `one_worker_per_gpu` loads one fitting model per T4 and deterministically
  shards rows.
- `device_map_auto` loads one larger model across both GPUs with one worker.
- 4-bit/8-bit modes use explicit `BitsAndBytesConfig` and require
  `bitsandbytes` during dependency preflight.
- Actual parameter dtype, quantization, device assignment, library/CUDA
  versions, and topology are recorded. No silent dtype substitution is
  accepted for unquantized models.

## Prompt, length, and generation

For `chat_template`, the tokenizer must expose a template; the adapter uses
explicit system/user messages and adds the generation prompt. For
`plain_text`, the same canonical system/user content is flattened
deterministically.

The adapter tokenizes without truncation. It rejects any row for which prompt
tokens plus maximum new tokens exceed the effective context window.
Generation is sampling-off with frozen temperature, top-p/top-k, token limit,
seed, EOS, and pad behavior.

## Execution

1. Run all cells with both gates false and confirm 58 synthetic tests pass
   with zero network/model/real-row activity.
2. Review source/manifest hashes, prompt/parser versions, retry/error gates,
   source mode, provider/model/revision, transport, dtype, quantization,
   context window, and output paths.
3. Only after separate authorization, set both the notebook
   `RUN_REAL_INFERENCE=True` and config `run_real_inference=true`.
4. Run from the top. Do not edit prompt, config, parser, thresholds, retry
   rules, or sample after outputs appear.
5. Shard attempt files are append-only. Each attempt key is
   `(run_id,row_id,attempt)`. Successful and other terminal rows never rerun;
   only budget-eligible parse/provider failures resume.
6. Routing rejection is not retried. The frozen
   `quarantine_run_continue` policy preserves remaining diagnostic records
   while making the whole run scientifically invalid.
7. Checkpoints, merged attempts, final terminal rows, and runtime metadata use
   atomic replacement. A partial JSONL tail or corrupt checkpoint is fatal.
8. Run `POST_RUN_ANALYSIS.py` with config, attempts, finals, source, manifest,
   and prompt template. Do not package unless every strict gate passes.
9. Set `PACKAGE_RESULT_ZIP=True` only after the saved analysis says
   `scientifically_valid=true`.

Do not commit raw outputs automatically. A later review must check routing,
privacy, model identity, completeness, and bounded interpretation.
