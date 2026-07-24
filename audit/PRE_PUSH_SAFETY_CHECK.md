# Pre-Push Safety Check

## Repository gate

- Target: `https://github.com/Saket-Maganti/raghal`
- Visibility: **PUBLIC**
- Remote state before ingest: **empty**
- Authenticated permission: **ADMIN**
- Intended branch: `main`
- Force push: **No**

## Staged-tree checks

- Tracked files before this report: **2,212**
- Tracked content size before this report: **155,419,683 bytes**
- Largest staged file: **13,965,462 bytes**
- Files at or above GitHub's 100 MiB hard limit: **0**
- Nested `.git` paths staged: **0**
- High-confidence token/private-key matches: **0**
- Absolute `/Users/<name>/` path matches: **0**
- Included source files covered by `SOURCE_SNAPSHOT_MANIFEST.sha256`: **2,190**
- Snapshot checksum verification: **PASS**
- Original nested Git worktree status: clean `main...origin/main`

## Exclusion gate

- Excluded or held source files: **200**
- Credential findings: **0**
- Owner identity/email findings: **58**
- Absolute home-path findings: **21**
- Generated Chroma database: excluded and hashed
- Internal assistant/revision and private submission material: excluded and hashed
- Nested Git internals: excluded; textual state exported

See `EXCLUDED_FILES_MANIFEST.csv`, `LARGE_OR_EXTERNAL_ASSETS_MANIFEST.csv`, and `SECRET_SCAN_SUMMARY.md`.

## Integrity notes

`git diff --cached --check` reports existing CRLF CSV endings, trailing spaces, and blank lines in preserved source snapshots. The non-CSV check reports 352 legacy whitespace/blank-line observations. These are not silently reformatted because byte-level preservation and scientific provenance take priority. They are not credential or GitHub-size failures.

The automated gate cannot establish redistribution rights. The missing project-wide license, FinanceBench non-commercial terms, and third-party dataset/paper/archive rights remain documented manual concerns.

## Decision

**PASS for a forensic public snapshot with explicit exclusions and license warnings.** No credential, private home path, nested Git directory, or GitHub-hard-limit file is staged. Re-run the staged scans after adding this report and before push.
