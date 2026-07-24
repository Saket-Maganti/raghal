# ControlledRAG Revision Summary

Date: 2026-04-30
Branch: `neurips-controlledrag-review-fixes`

## Files Changed

- Main paper:
  - `papers/paper_neurips/main.tex`
  - `papers/paper_neurips/sections/controlledrag_abstract.tex`
  - `papers/paper_neurips/sections/controlledrag_main.tex`
- Supplement:
  - `papers/paper_neurips/supplement.tex`
- Bibliography and trace files:
  - `papers/paper_neurips/references.bib`
  - `papers/paper_neurips/SOURCE_TRACE.md`
  - `papers/paper_neurips/CLAIMS_AUDIT.md`
  - `papers/paper_neurips/REVISION_PLAN_CONTROLLEDRAG.md`
  - `papers/paper_neurips/REVISION_SUMMARY_CONTROLLEDRAG.md`
- Generated PDFs:
  - `papers/paper_neurips/main.pdf`
  - `papers/paper_neurips/main_submission.pdf`
  - `papers/paper_neurips/supplement.pdf`
  - `papers/paper_neurips/supplement_submission.pdf`

## Scripts Added

- `scripts/compute_standardized_scorer_fragility.py`
- `scripts/select_human_disagreement_cases.py`
- `scripts/analyze_human_disagreement_labels.py`
- `scripts/compute_cost_headtohead_cis.py`
- `scripts/compute_matched_ccs_distribution.py`

All five scripts pass `python3 -m py_compile`.

## Results Generated

- `results/revision/fix_03/standardized_scorer_fragility.csv`
  - Adds raw, z-score, and rank-normalized scorer contrasts with paired bootstrap CIs.
- `results/human_disagreement_expansion/annotation_batch_disagreement_100.csv`
  - Selects 100 high-disagreement cases for targeted human calibration.
- `results/human_disagreement_expansion/README.md`
  - Documents selection logic, annotation labels, and downstream analysis.
- `results/human_disagreement_expansion/analysis_summary.csv`
  - Correctly handles missing labels; status marked as pending in `analysis_summary.md`.
- `results/human_disagreement_expansion/batch_composition.csv`
- `results/human_disagreement_expansion/scorer_score_summary.csv`
- `results/human_disagreement_expansion/missing_human_labels_report.md`
  - Descriptive statistics and completion tracking for the disagreement batch.
- `results/human_disagreement_expansion/human_eval_instructions.md`
- `results/human_disagreement_expansion/human_eval_codebook.md`
- `results/human_disagreement_expansion/human_eval_rater1.csv`
- `results/human_disagreement_expansion/human_eval_rater2.csv`
- `results/human_disagreement_expansion/human_eval_adjudication_template.csv`
  - Complete human evaluation package ready for independent annotation.
- `results/revision/fix_06/h2h_summary_with_ci.csv`
  - Adds bootstrap CIs for faithfulness and Wilson CIs for hallucination in the small cost-aware head-to-head cell.
- `results/revision/fix_01/matched_ccs_faithfulness_quantiles.csv`
- `results/revision/fix_01/matched_ccs_threshold_rates.csv`
  - Adds distributional diagnostics for the matched-CCS null.

## Paper Changes

- Reframed ControlledRAG as a reporting/audit standard, not a new RAG method.
- Replaced unsafe cross-scorer "effect size" phrasing with raw-score, standardized, rank-normalized, or score-scale-dependent contrast language.
- Added a seven-axis ControlledRAG audit map.
- Strengthened metric-fragility framing: fixed generations, fixed retrieval condition, scorer-only variation, scorer correlations, and standardized contrasts.
- Clarified scorer implementation details, including the legacy NLI-style zero-shot proxies and the local context-conditioned RAGAS-style judge.
- Added related-work positioning against ARES, RAGChecker, RAGTruth, MIRAGE, FaithJudge, RAGAS, TRUE, and SummaC without presenting ControlledRAG as a replacement.
- Defined CCS, HCPC-v1/v2, answer-span indicator, faithfulness, hallucination, RAGAS-style scoring, threshold-transfer recovery, and cost.
- Clarified threshold-transfer recovery units and why values can be negative or exceed 1.
- Clarified the matched-CCS null and the distinction between mean faithfulness and thresholded hallucination tails.
- Clarified that lexical answer-span presence is a weak proxy, not gold evidence support.
- Reworded the cost-aware baseline section to avoid leaderboard-style winner claims.
- Kept long-form QASPER/MS-MARCO as exploratory supplement-only scope-limit evidence.

## Not Done

- No broad human study was run.
- No human-disagreement results are claimed in the paper or supplement because the new 100-case batch is not labeled yet.
- No QASPER/MS-MARCO expansion was run.
- No paid APIs, remote judges, Groq quota, or large model downloads were used.
- Optional Llama-3 tiny sanity check was not run. `llama3:latest` is locally installed, but there is no cheap existing fixed-context, three-scorer runner, and adding/running one would distract from the professor-requested paper fixes.

## Human Annotation TODO

1. Fill `results/human_disagreement_expansion/annotation_batch_disagreement_100.csv`.
2. Re-run `python3 scripts/analyze_human_disagreement_labels.py`.
3. Add results to the supplement only after labels are complete.

## Build Status

- Main build:
  - `pdflatex -interaction=nonstopmode main.tex`
  - `bibtex main`
  - `pdflatex -interaction=nonstopmode main.tex`
  - `pdflatex -interaction=nonstopmode main.tex`
- Supplement build:
  - `pdflatex -interaction=nonstopmode supplement.tex`
  - `bibtex supplement`
  - `pdflatex -interaction=nonstopmode supplement.tex`
  - `pdflatex -interaction=nonstopmode supplement.tex`

Final log check found no undefined citations/references and no overfull boxes. `main.pdf` is 12 pages; `supplement.pdf` is 8 pages.

## Git / Push

- Commit and push are performed after this summary is written; the final
  assistant response records the final commit hash and push result.
- Unrelated root-level deletes and untracked folders were present before
  staging this revision and were intentionally left unstaged.
