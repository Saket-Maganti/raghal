# Repaired Build-Only Modern Judge Package

Status: `PREPARED_NOT_EXECUTED`.

The optional package is hardened for a later separately authorized run. Prompt
05 repair added canonical injection-resistant prompt v2 rendering,
score-derived labels, typed failures, bounded retries, correct resume state,
append-only attempt keys, atomic persistence, explicit model-source modes,
T4/dtype and quantization checks, chat-template/plain-text transport,
reject-on-overlength context handling, schema-v2 provenance, strict
complete-pair validity gates, and adversarial synthetic tests.

No real model, API, network judge, model download, Kaggle/Colab job, GPU
inference, or real-row scoring was performed. The rebuttal remains complete
without this optional result.

Start with:

- `REPAIR_AUDIT_BEFORE.md` and `REPAIR_CHANGELOG.md`;
- `PRE_REGISTRATION.md` for the frozen scientific contract;
- `RUN_CONFIG_TEMPLATE.json`, which is deliberately non-runnable;
- `KAGGLE_RUNBOOK.md` or `API_RUNBOOK.md`;
- `RESULT_INGESTION_RUNBOOK.md` for strict acceptance gates; and
- `REPAIR_VALIDATION_REPORT.md` / `REPAIR_RED_TEAM_REPORT.md`.

Core implementation:

- `prompt_rendering.py` — the only prompt renderer;
- `run_config.py` — immutable config/source-mode validation;
- `judge_execution.py` — typed attempts and retry loop;
- `run_state.py` — resume, uniqueness, terminal state, atomic writes;
- provider adapters — hard-pinned API and Hugging Face transports;
- `POST_RUN_ANALYSIS.py` — no-silent-shrinkage validity gating; and
- `OUTPUT_SCHEMA.json` — closed schema for every attempt/final record.

Candidate manifests remain deterministic, nested, text-free, and unchanged.
