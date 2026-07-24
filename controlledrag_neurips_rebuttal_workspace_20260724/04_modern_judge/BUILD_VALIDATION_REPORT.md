# Build Validation Report

## Executed checks

| Check | Result |
| --- | --- |
| Python compilation for seven scripts | Pass |
| Actual fixed-source SHA and 600-row/condition structure | Pass |
| 300/400/500/600 candidate generation | Pass |
| Byte-for-byte deterministic regeneration | Pass |
| Candidate nestedness, uniqueness, and pair counts | Pass |
| CPU synthetic/mock adapter suite | Pass |
| Network calls during tests | 0 |
| Model loads during tests | 0 |
| Real rows scored during tests | 0 |
| Strict parser valid/invalid cases | Pass |
| Unexpected model/route/fallback rejection | Pass |
| Hugging Face model-load guard | Pass |
| Synthetic post-run paired analysis | Pass (`n=100` mock pairs) |
| Deterministic ZIP allow-list builder | Pass |
| JSON Schema Draft 2020-12 validation | Pass |
| Notebook JSON validation and eight code-cell compilation | Pass |
| Notebook default-path execution | Pass; synthetic suite ran and real flag remained false |
| Frozen prompt rendering and source/candidate hash gates | Pass |

## Important boundary

No notebook kernel, GPU, real model, model weight, external provider, API,
Kaggle job, Colab job, dataset download, or real inference was invoked.
Temporary synthetic ZIP/test files were not placed in the rebuttal workspace.

Status: `SYNTHETIC_VALIDATION_PASS`
