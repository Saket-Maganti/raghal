# Secret Scan Summary

- High-confidence credential findings: **0**
- Owner identity/email findings: **58 files**
- Absolute home-path findings: **21 files**

The scanner checked text files, small ZIP members, and text extracted from 50 PDFs for GitHub tokens, AWS access keys, OpenAI-style keys, private-key blocks, assigned credentials, owner email/identity strings, and macOS home paths.

No credential was found. Identity-bearing and home-path files were excluded from the public working trees, as were nested Git internals that contain author metadata. Exact paths, sizes, hashes, and reasons are in `EXCLUDED_FILES_MANIFEST.csv`.

Regex scanning is not a proof of absence. A second scan is run over the staged Git index before commit and push.
