# Submission Checklist

## Build

- Main source: `main.tex`
- Supplement source: `supplement.tex`
- Bibliography: `references.bib`
- Style status: no official `neurips*.sty` file is present in this
  directory; the current source uses the repository's existing
  NeurIPS-style review geometry. Before portal upload, verify against
  the official venue template.
- Expected build commands:
  - `pdflatex -interaction=nonstopmode main`
  - `bibtex main`
  - `pdflatex -interaction=nonstopmode main`
  - `pdflatex -interaction=nonstopmode main`
  - `pdflatex -interaction=nonstopmode supplement`
  - `bibtex supplement`
  - `pdflatex -interaction=nonstopmode supplement`
  - `pdflatex -interaction=nonstopmode supplement`

## Double-Blind Review

- Main and supplement use anonymous authors.
- Public release, benchmark, repository, archive identifiers, and
  personal links are not included in the review-version text.
- The artifact is described generically as an anonymized review package.

## NeurIPS Evaluations & Datasets Fit

- The paper is framed as an evaluation methodology and audit-protocol
  contribution.
- ControlledRAG is presented as a prescriptive minimum reporting
  standard, not as a new retriever, new scorer, or method leaderboard.
- Each major empirical result maps to one of the seven reporting axes.

## Claim Hygiene

- CCS is not described as causing or driving faithfulness.
- HCPC-v2 is not described as dominating or solving hallucination.
- Self-RAG is treated as a harness-mismatched appendix baseline only.
- Human calibration is not described as a settled scorer ranking.
- Long-form results are described as exploratory.

## Final Artifacts

- `main_submission.pdf`
- `supplement_submission.pdf`
