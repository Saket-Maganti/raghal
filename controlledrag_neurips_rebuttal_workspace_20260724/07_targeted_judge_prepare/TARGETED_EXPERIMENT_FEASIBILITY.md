
# Targeted experiment feasibility

Status: `READY_FOR_TARGETED_KAGGLE_EXECUTION`

Scientific support class:
`MAIN_PANEL_WITH_ONE_VALID_HUMAN_SLICE`.

## Provenance-first audit

Inspected the recovered fixed-output per-query source, its locked text-free
row/pair-ID manifest, the approved typical adjudicated/context file, the
approved disagreement-targeted two-rater-plus-adjudication file, human schema
crosswalks, prior scorer-input verification, and prior modern-judge repair
receipts.

| Gate | Candidate | Eligible | Result |
| --- | ---: | ---: | --- |
| Main fixed outputs | 600 | 600 | passes hard minimum |
| Raw baseline/HCPC-v1 pairs | 200 | 200 | complete raw outputs |
| Preregistered primary pairs | 200 | 194 | locked historical intersection |
| Typical human slice | 99 | 83 | passes ≥80; 16 intermediate labels excluded |
| Disagreement-targeted slice | 100 | 72 | diagnostic only after deduplication |

Major exclusions:

- cross-panel semantic duplicate of a main-panel row: 4
- duplicate semantic row under another example ID: 24
- intermediate ternary label has no approved binary mapping: 16

The same-row human bridge is scientifically valid for the 83 determinate
typical rows only. The disagreement-targeted slice is retained as a diagnostic
and cannot be presented as a robust rebuttal bridge. Human slices are never
pooled.

Model revision is locked to `a09a35458c702b33eeacc393d103063234e8bc28`. Prompt symmetry passes.
Preregistration is frozen. All local synthetic tests and the preparation-only
notebook path pass. The private ZIP exists, verifies, is outside Git, and
requires a manual private Kaggle upload. No real inference occurred.
