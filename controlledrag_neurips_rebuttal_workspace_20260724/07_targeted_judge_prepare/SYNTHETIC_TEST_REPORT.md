
# Synthetic test report

Status: `PASS`

Twenty-four passing test methods across the eight required test modules
exercise all 26 required synthetic cases,
including strict parsing, fences, extra/missing keys, type/range failures,
duplicate/missing/mismatched outputs, model/interface/checksum mismatches,
paired/unpaired rows, separate human slices, truncation boundary,
semantic deduplication, differential missingness, deterministic bootstrap and
sharding, deterministic ZIP packaging, and the no-real-inference gate.

Fixtures contain no real paper rows. No network inference, model import,
weight download, or real row scoring occurs.
