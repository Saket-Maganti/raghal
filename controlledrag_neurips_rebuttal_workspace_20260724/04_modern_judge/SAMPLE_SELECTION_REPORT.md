# Sample Selection Report

## Outcome

Four deterministic, nested, text-free candidate manifests were built from
the provenance-approved fixed 600-row panel. The source SHA-256 was verified
as `78348a4a786434fbf5aa42e1179f7c81aae7695eaee4e876d145aa3cb1a575f4`
before selection.

| Candidate | Condition counts (baseline / HCPC-v1 / HCPC-v2) | Complete three-condition groups | Complete baseline–HCPC-v1 pairs | Manifest SHA-256 |
| ---: | --- | ---: | ---: | --- |
| 300 | 100 / 100 / 100 | 100 | 100 | `a09e22ca746dd5c73efdfa50a9e24e2107952a26a60df3d869ce8044be4c6f04` |
| 400 | 134 / 133 / 133 | 133 | 133 | `4b397bff1fc1ea26918444d4857a71d5e823eb43ba4c5517b5e8781ea5a18a3e` |
| 500 | 167 / 167 / 166 | 166 | 167 | `6c3a2e63137507c3c9673658584ced60f70d4e672985d69b10ec0d8561ffee67` |
| 600 | 200 / 200 / 200 | 200 | 200 | `60081570d1801d7e9ab242d98128898e89fc0135b509b83d61561f5aa039e3e1` |

Selection ranks the 200 query groups by SHA-256 with the frozen salt
`controlledrag-modern-judge-v1`, includes complete groups first, and uses at
most two deterministic condition-ordered extras to hit 400 or 500 exactly.
Each smaller candidate is a strict subset of each larger candidate.

## Privacy and content

Manifests contain:

- candidate size and position;
- source row index;
- stable row and pair IDs;
- input digest;
- condition, dataset, source seed, and generator label;
- locked source SHA-256.

They contain no question, ground truth, answer, context, prior scorer value,
human label, rater information, or model output.

## Determinism checks

A second build into a temporary directory matched all four committed CSVs and
the candidate index byte-for-byte. All manifest row IDs are unique and the
expected nestedness, condition balance, source hash, and pair counts passed.

Status: `DETERMINISTIC_CANDIDATES_READY_NOT_SCORED`
