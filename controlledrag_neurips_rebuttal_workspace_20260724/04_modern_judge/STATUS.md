# Modern Judge Package Status

`PREPARED_NOT_EXECUTED`

- Candidate manifests: ready for 300, 400, 500, and 600 rows.
- Prompt/parser/output schema: frozen build version ready.
- FreeLLMAPI-style adapter: mock-tested with strict routing rejection.
- Hugging Face adapter: load guard and configuration paths mock-tested.
- Kaggle T4×2 notebook: JSON-valid and code cells compile; real flag defaults
  to false.
- Checkpoint/resume, duplicate rejection, raw/parsed logs, post-run analysis,
  and deterministic result ZIP: implemented.
- Real inference, network/API calls, model downloads, Kaggle/Colab launches,
  and GPU runs: not performed.
- Scientific dependency: optional; the rebuttal remains complete without a
  modern-judge result.

Unresolved before any later execution:

1. final candidate size;
2. local Hugging Face versus hard-pinned API route;
3. exact provider and exact model/revision;
4. allowed returned-model and route metadata;
5. quantization, dtype, and GPU strategy;
6. model license/access and current API pricing/rate limits.
