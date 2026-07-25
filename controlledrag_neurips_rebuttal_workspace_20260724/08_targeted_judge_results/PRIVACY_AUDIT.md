# Privacy audit

Public Prompt B files contain only:

- aggregate counts and metrics;
- confidence intervals and finite-replicate counts;
- model and immutable revision;
- repair and inclusion descriptions;
- claim decisions and response prose.

They contain no questions, contexts, answers, row identifiers, human annotation rows, rater identity, raw judge text, ZIP contents, local paths, screenshots, credentials, or confidential review quotations.

The confidential paper PDF, frozen input bundle, accepted output ZIP, extracted records, and independent recomputation script remain outside Git.

Public source cleanup removed row-level human files, row-level result tables, raw JSONL data, generated ZIPs, and legacy scripts that depended on private material. Backup refs preserve provenance.

Status: `PRIVATE_DATA_SCAN_PASS`, `IDENTITY_LEAK_SCAN_PASS`, `ABSOLUTE_PATH_SCAN_PASS`.
