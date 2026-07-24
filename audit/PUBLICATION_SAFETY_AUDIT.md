# Publication Safety Audit

The target repository is confirmed **public**. Publication filtering therefore takes precedence over copying private quarantine material byte-for-byte.

## Gate result

- Source files inventoried: **2,390**
- Files included in the four publication trees: **2,190**
- Files excluded or held for manual review: **200**
- High-confidence credential findings: **0**
- Files containing owner identity/email patterns: **58**
- Files containing absolute macOS home paths: **21**
- PDF files text-extracted with `pdftotext`: **50**
- Files containing prompt-injection phrases: **4**
- Nested repositories detected: `rag-hallucination-detection_main`

Every excluded file is represented by source folder, relative path, byte size, SHA-256, and reason in `EXCLUDED_FILES_MANIFEST.csv`.

## Material excluded

- Nested `.git/` internals; branch, commit, status, log, tags, remotes, submodule, shallow, ignored, and LFS state are exported as text.
- `.DS_Store`, bytecode, pytest caches, and the generated 69 MB Chroma database.
- Owner names, handles, personal emails, or absolute home paths in paper copies, metadata, notebooks, scripts, logs, and release material.
- Internal assistant/revision documents and private OpenReview/submission checklists under `deleted_from_head/`.
- The personal adjudication authoring script `moved_from_repo/human_eval_final/scripts/complete_human_eval.py`.

The scientific and process existence of these files is not hidden: paths and hashes remain in the manifests, while the original local trees are unchanged.

## Prompt-injection review

The phrase `system prompt` occurs in:

- `moved_from_repo/papers/paper_longform/sections/mechanistic.tex`
- `moved_from_repo/papers/ragpaper/sections/mechanistic.tex`
- two author-identifying compiled PDFs that were excluded

The included occurrences are ordinary scientific discussion, not instructions to the audit agent. They are preserved as inert source text. Separately, `src/ragas_scorer.py` interpolates question, context, and answer into a judge prompt without a dedicated injection-isolation mechanism; this is a scientific robustness concern, not a publication secret.

## Human data

Human-evaluation CSVs use opaque rater labels and public QA content. No email, Prolific ID, or direct participant identifier was located. The n=99 and n=100 label schemas differ and must not be silently pooled.

## Residual manual review

- The repository has no project-wide license; two MIT licenses apply only to release subtrees.
- Dataset, PDF, archive, and generated model-output redistribution rights still require owner confirmation.
- Publishing any identity-linked copy during double-blind review can create anonymity risk even if no credential is present.
- Automated scanning reduces risk but does not prove absence; the staged tree receives a final regex and size scan before push.
