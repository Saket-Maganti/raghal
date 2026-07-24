# Kaggle T4×2 Runbook

## Current state

Do not interpret these instructions as an executed run. Prompt 05 stopped at
`PREPARED_NOT_EXECUTED` and tested only mocks/synthetic rows.

## Before opening Kaggle

1. Choose exactly one candidate size before inspecting any modern-judge
   output. Prefer 600 if the selected model fits the budget.
2. Copy `RUN_CONFIG_TEMPLATE.json` to `run_config.json` outside Git.
3. Replace every `PIN_...`/`SET_...` value. `model="auto"` is forbidden.
4. Pin the Hugging Face model to `model_id@immutable_revision`.
5. Choose one declared loading mode: 4-bit, 8-bit, BF16, or FP16.
6. Keep `run_real_inference=false` while uploading and run the synthetic cell.
7. Upload the fixed source CSV separately and verify its SHA-256 is
   `78348a4a786434fbf5aa42e1179f7c81aae7695eaee4e876d145aa3cb1a575f4`.

Do not upload credentials, historical caches, model checkpoints, or human
rater files.

## Kaggle settings

- Accelerator: GPU T4 ×2.
- Internet: enable only if the pinned model must be downloaded and the run is
  authorized. Otherwise retain `local_files_only=true`.
- Persistence: use the working directory for results, not the dataset mount.
- Secrets: use Kaggle Secrets only if a gated model token is required; never
  write the token to config, notebook output, checkpoints, or ZIP files.

## Strategy selection

- Use `one_worker_per_gpu` when one copy of the pinned model fits on a single
  16 GB T4. The notebook creates one worker per detected GPU and shards rows
  deterministically.
- Use `device_map_auto` for a larger model that must span both GPUs. Only one
  worker may own the model.
- Use 4-bit/8-bit when declared in advance and supported by the pinned model.
  BF16 on T4 may be unsupported or slower; FP16 is the safer native T4
  floating-point option. Record the actual dtype selected by the runtime.

The notebook records whether exactly two T4 devices were detected and refuses
the two-worker strategy on a different topology.

## Execution

1. Restart the Kaggle session and run all cells with
   `RUN_REAL_INFERENCE=False`.
2. Confirm the synthetic test reports zero network calls/model loads.
3. Review the frozen prompt, manifest hash, run ID, provider/model/revision,
   quantization, dtype, fallback limit, and output paths.
4. Change both `RUN_REAL_INFERENCE=True` in the notebook and
   `run_real_inference=true` in `run_config.json`.
5. Run from the top. Do not edit the prompt or parser after seeing outputs.
6. If interrupted, retain shard/final JSONL and checkpoint files, restart with
   `resume=true`, and verify duplicate rejection.
7. Run `POST_RUN_ANALYSIS.py`. Stop if `scientifically_valid` is false.
8. Run `BUILD_RESULT_ZIP.py` only on the allow-listed result directory.

## After execution

Download the result ZIP and its printed SHA-256. Do not commit raw results
until Prompt 6 validates routing, completeness, privacy, model identity,
source hashes, and interpretation. Never overwrite the candidate manifests.
