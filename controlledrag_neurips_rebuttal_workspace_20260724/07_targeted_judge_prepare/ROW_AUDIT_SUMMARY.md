
# Row audit summary

- Main: 600/600 eligible fixed rows, 200 raw baseline/HCPC-v1 pairs, 194
  locked primary comparison pairs.
- Typical: 99 adjudicated ternary rows; 83 determinate binary rows eligible;
  16 `partially_supported` rows excluded rather than recoded.
- Disagreement-targeted: 100 adjudicated binary records; 24 within-slice
  semantic duplicates removed; four additional cross-panel semantic
  duplicates removed; 72 diagnostic rows remain.
- Frozen union: 755 unique semantic rows and 1,510 requested interface
  outputs.
- Label convention: typical `supported=1`, `unsupported=0`;
  disagreement `faithful=1`, `hallucinated=0`.
- Approved historical AP lock remains
  `0.764813 / 0.928793 / 0.859367`; it is not recomputed on the deduplicated
  diagnostic panel and is not pooled with the typical slice.
- Every private row records a relative provenance source and canonical source
  payload SHA-256. Source-file hashes are separately frozen.
