# Build-Only Modern Judge Package

Status: `PREPARED_NOT_EXECUTED`.

This directory contains an optional, hard-pinned modern-judge execution
package for later authorized use. Prompt 05 performed only deterministic
sample selection and synthetic/mock tests. It did not load model weights,
run inference, call a provider, contact Kaggle/Colab, or download data.

The rebuttal remains complete without any result from this package.

Start with:

- `PRE_REGISTRATION.md` for the frozen scientific plan;
- `KAGGLE_RUNBOOK.md` or `API_RUNBOOK.md` for later execution;
- `RUN_CONFIG_TEMPLATE.json` for explicit provider/model pinning;
- `RESULT_INGESTION_RUNBOOK.md` for post-run acceptance gates; and
- `STATUS.md` for the current execution state.

Candidate manifests contain only row identifiers, join indices, grouping
metadata, and hashes. Raw question/context/answer text remains in the
provenance-approved source table and is joined only at execution time.
