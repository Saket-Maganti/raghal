# Modern Judge Package Status

`PREPARED_NOT_EXECUTED`

Repair status: `PROMPT_05_REPAIRED_PREPARED_NOT_EXECUTED`.

- Candidate manifests: unchanged and ready at 300/400/500/600 rows.
- Prompt/parser: hardened v2 with canonical escaping and derived labels.
- Retry/resume/error typing: implemented and adversarially tested.
- Strict scientific gates: zero-error defaults and complete-pair reporting.
- Model source: explicit offline snapshot or authorized pinned download.
- T4×2: FP16-preferred, BF16 rejected, explicit quantization configuration.
- Prompt transport: plain text or tokenizer chat template, frozen in config.
- Context: token-counted and rejected if too long; no silent truncation.
- Persistence: append-only logical attempts and atomic state/final writes.
- Schema: closed v2 provenance contract for attempts and finals.
- Notebook: both real-run gates false; default path runs synthetic tests only.
- Synthetic tests: 58 passed, 0 failed.
- Network calls: 0.
- Model loads/downloads: 0.
- Real rows scored: 0.

Before any later run, the author must separately choose and authorize the
candidate, exact model/provider/revision, source mode, transport,
quantization/dtype/strategy, primary pair minimum, licensing, access, and
cost/rate limits.
