# ControlledRAG Revision Plan

Date: 2026-04-30
Branch: `neurips-controlledrag-review-fixes`

## Files Found

- Main paper: `main.tex`
- Main paper body: `sections/controlledrag_main.tex`
- Main abstract: `sections/controlledrag_abstract.tex`
- Supplement: `supplement.tex`
- Bibliography: `references.bib`
- Figures: `figures/`
- Local source trace: `SOURCE_TRACE.md`
- Claim hygiene notes: `CLAIMS_AUDIT.md`
- Submission checklist: `SUBMISSION_CHECKLIST.md`
- Audit log: `audit_log.md`
- Result roots used by this revision:
  - `../../results/revision/fix_01/`
  - `../../results/revision/fix_02/`
  - `../../results/revision/fix_03/`
  - `../../results/revision/fix_04/`
  - `../../results/revision/fix_05/`
  - `../../results/revision/fix_06/`
  - `../../results/revision/fix_11/`
  - `../../results/revision/fix_12/`
  - `../../results/revision/fix_13/`
  - `../../results/revision/fix_14/`
  - `../../results/revision/fix_15/`
  - `../../results/human_eval/`
- Relevant existing experiment scripts:
  - `../../experiments/fix_03_multimetric_faithfulness.py`
  - `../../experiments/fix_04_tau_generalization.py`
  - `../../experiments/fix_06_baseline_h2h_pareto.py`
  - `../../experiments/fix_12_answer_span_diagnostic.py`
  - `../../experiments/fix_13_retriever_sanity.py`
  - `../../experiments/fix_14_second_generator_metric_fragility.py`
  - `../../experiments/fix_15_longform_stress.py`

## Planned Edits

- Reframe the paper around ControlledRAG as a reporting/audit standard, not a RAG method.
- Replace unsafe cross-scorer "effect size" language with raw-score or score-scale-dependent contrast language unless standardized values are computed.
- Strengthen the metric-fragility section by emphasizing fixed generations, fixed retrieval condition, scorer descriptions, scorer correlations, and the takeaway that scorer choice is an audit axis.
- Add or tighten definitions for CCS, HCPC-v1/v2, faithfulness, hallucination, answer-span indicator, RAGAS-style judging, threshold-transfer recovery, and cost.
- Add a compact ControlledRAG seven-axis audit map.
- Clarify threshold-transfer recovery and why values can be negative or exceed one.
- Clarify the matched-CCS null: continuous means and thresholded hallucination rates measure different distributional properties.
- Clarify the answer-span/control diagnostic and keep span presence as a weak proxy, not a gold support variable.
- Keep the cost-aware baseline section as deployment-identifiability evidence rather than a leaderboard.
- Keep QASPER/MS-MARCO as an exploratory, supplement-only scope limitation.
- Update `SOURCE_TRACE.md` and artifact notes for new scripts/results.

## Scripts and Runs Completed

- Added and ran `../../scripts/compute_standardized_scorer_fragility.py`.
  - Output: `../../results/revision/fix_03/standardized_scorer_fragility.csv`.
  - Result: raw, z-score, and rank-normalized baseline--HCPC-v1 and HCPC-v2--HCPC-v1 contrasts with paired bootstrap CIs.
- Added and ran `../../scripts/select_human_disagreement_cases.py`.
  - Output: `../../results/human_disagreement_expansion/annotation_batch_disagreement_100.csv`.
  - Output: `../../results/human_disagreement_expansion/README.md`.
  - Result: 100 targeted scorer-disagreement examples, balanced across baseline/HCPC-v1/HCPC-v2 and disagreement strata where available.
- Added and smoke-ran `../../scripts/analyze_human_disagreement_labels.py`.
  - Output: `../../results/human_disagreement_expansion/analysis_summary.csv`.
  - Output: `../../results/human_disagreement_expansion/batch_composition.csv`.
  - Output: `../../results/human_disagreement_expansion/scorer_score_summary.csv`.
  - Output: `../../results/human_disagreement_expansion/missing_human_labels_report.md`.
  - Result: Correctly handles missing labels by reporting composition and score statistics while marking human-alignment metrics as pending.
- Prepared human evaluation package.
  - Output: `../../results/human_disagreement_expansion/human_eval_instructions.md`.
  - Output: `../../results/human_disagreement_expansion/human_eval_codebook.md`.
  - Output: `../../results/human_disagreement_expansion/human_eval_rater1.csv`.
  - Output: `../../results/human_disagreement_expansion/human_eval_rater2.csv`.
  - Output: `../../results/human_disagreement_expansion/human_eval_adjudication_template.csv`.
  - Result: Standardized protocol, instructions, and templates ready for independent annotation.
- Added and ran `../../scripts/compute_cost_headtohead_cis.py`.
  - Output: `../../results/revision/fix_06/h2h_summary_with_ci.csv`.
  - Result: bootstrap CIs for mean faithfulness and Wilson CIs for hallucination rates in the small head-to-head cost cell.
- Added and ran `../../scripts/compute_matched_ccs_distribution.py`.
  - Outputs: `../../results/revision/fix_01/matched_ccs_faithfulness_quantiles.csv` and `../../results/revision/fix_01/matched_ccs_threshold_rates.csv`.
  - Result: quantile and threshold-rate diagnostics explaining why a null mean contrast can coexist with threshold-sensitive hallucination differences.
- Checked local Ollama availability with `ollama list`.
  - `llama3:latest` is installed.
  - The optional Llama-3 tiny run was not executed because the repo does not expose a cheap fixed-context, three-scorer Llama runner; adding one plus running 150 generations/judgments would distract from the professor's requested paper fixes.
- Built `main.pdf`, `main_submission.pdf`, `supplement.pdf`, and `supplement_submission.pdf` with the existing LaTeX command sequence from this folder.

## Experiments Explicitly Not Run

- No broad new human study: the only human-eval expansion is a targeted disagreement-case annotation artifact.
- No expansion of QASPER/MS-MARCO long-form stress tests: these remain exploratory scope-limit evidence.
- No paid APIs, paid judges, Groq quota burn, or remote model calls.
- No automatic download of large Llama models.
- No optional Llama-3 tiny check in this pass: although `llama3:latest` is installed locally, a cheap existing fixed-context runner was not available and the extra run would be a distraction from the main reviewer-proofing work.
- No additional broad generator panel beyond the already completed Qwen2.5 compact replication.
- No new retrieval-method leaderboard: the cost-aware section will remain an audit of deployment degrees of freedom.

## Remaining Human Work

- Fill `../../results/human_disagreement_expansion/annotation_batch_disagreement_100.csv` with human labels.
- Re-run `../../scripts/analyze_human_disagreement_labels.py` after annotation.
- Only then add any human-disagreement expansion results to the paper or supplement.
