
# Expected output contract

The run must produce `CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT/` and the
deterministic `CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT.zip`, including run,
environment, model-identity, checksum, and final-configuration receipts; two
append-only GPU shards and their merged file; explicit invalid, missing,
duplicate, and differential-missingness reports; all preregistered analysis
CSVs; bounded rebuttal tables; logs; and SHA-256 checksums.

Every one of 1,510 requested `(experiment_row_id, interface)` keys must be
accounted for. Invalid raw text is preserved. Model revision mismatches,
duplicates, unexpected IDs, and silent precision/truncation changes are fatal.
