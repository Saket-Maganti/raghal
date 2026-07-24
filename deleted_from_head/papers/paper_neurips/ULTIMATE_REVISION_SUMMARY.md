# Ultimate Revision Summary — NeurIPS ControlledRAG paper

This document summarises the senior-reviewer polish pass that produced
the current `papers/paper_neurips/` state. Companion plan:
[`ULTIMATE_REVISION_PLAN.md`](ULTIMATE_REVISION_PLAN.md).

## High-level outcome

- Broken abstract fixed (Qwen2.5 third value `0.134` restored, scaled
  audit lead-in restored, abstract rewritten as a single readable
  block under the limit).
- Section 8 fully restored and strengthened: completed `n=99`
  two-pass annotation calibration (\S 8.1) plus the targeted
  scorer-disagreement batch \S 8.2 with prepared-but-pending labels.
- Legacy zero-shot DeBERTa / `roberta-large-mnli` rows are
  consistently labelled as legacy zero-shot label proxies, with the
  context-not-consumed implementation noted in §3 (Setup),
  §7 (Metric Fragility), and the supplement.
- Context-conditioned NLI rescoring **was actually run** on a balanced
  $n=600$ subset and on the $n=99$ calibration items. Both DeBERTa-v$3$
  and `roberta-large-mnli` produce **sign-flipped** baseline$-$HCPC-v$1$
  contrasts under context-conditioned calling on the same fixed
  generations; CIs are disjoint between legacy and context-conditioned
  formats for both backbones. This is now an empirically observable
  audit axis, not just a disclosure axis.
- Both PDFs build cleanly (`main.pdf`: 14 pages; `supplement.pdf`: 12
  pages) with no undefined references.

## Files changed

### Paper text
- `papers/paper_neurips/sections/controlledrag_abstract.tex` — full
  rewrite. Single-block abstract that lists the metric-fragility
  triple, the Qwen2.5 ordering (now including the missing `0.134`),
  the $n=99$ two-pass calibration ($\kappa=0.774$), the prepared
  $100$-example disagreement batch with explicit pending status, the
  matched CCS null, the scaled-audit shrinkage, the threshold-transfer
  table, and the cost-aware result. ControlledRAG named at the end.
- `papers/paper_neurips/sections/controlledrag_main.tex` —
  - Six-contribution list (was five) with explicit Human Calibration
    contribution.
  - Audit-map table cell for "Human calibration" updated.
  - Seven-axis paragraph block in §4 collapsed into one
    runs-the-reader paragraph (the redundant enumerate was removed).
  - §7 (Metric Fragility) has a new "Scorer input format is itself an
    audit axis" paragraph reporting the $n=600$ context-conditioned
    rescoring sign-flip; legacy / context-conditioned phrasing is
    consistent.
  - Table~\ref{tab:metric_fragility_main} relabels the rows as
    "Legacy DeBERTa proxy (no context)" / "Legacy
    \texttt{roberta-large-mnli} proxy (no context)" /
    "Context-conditioned RAGAS-style judge".
  - §8 fully rebuilt: \S 8.1 Completed annotation calibration ($n=99$)
    with table reporting $\kappa=0.774$, raw agreement $0.919$, label
    distribution $79/16/4$, and Spearman / Kendall / Pearson
    correlations with bootstrap $95\%$ CIs.
  - §8.2 Targeted scorer-disagreement batch ($n=100$, labels pending)
    with explicit prepared-but-pending status and analysis-script
    description.
  - §Discussion expanded with a new paragraph on what scorer
    alignment is and is not, and a "Where the audit stops short"
    paragraph that calls out three gaps (one-generator Qwen2.5
    panel, $40$-question long-form probe, unlabelled $100$-batch).
  - §Limitations: human-evaluation paragraph rewritten to reflect both
    arms; ethics paragraph updated to clarify that no annotator data
    is included with the unlabelled $100$-batch.
- `papers/paper_neurips/supplement.tex` —
  - Pre-registration paragraph rewritten to describe both human-eval
    arms as separate pre-registered axes.
  - New section \texttt{supp:human\_calibration} with the full $n=99$
    calibration table (Spearman / Pearson / Kendall, bootstrap $95\%$
    CIs) and source-file listing.
  - New section \texttt{supp:human\_disagreement} for the
    targeted $100$-example disagreement batch with prepared-but-pending
    status.
  - New section \texttt{supp:context\_conditioned\_nli} containing the
    context-conditioned rescoring contrasts table on the $n=600$
    subset, the $n=99$ alignment-with-adjudicated-labels readout,
    bootstrap CIs, and explicit "subset is not full table" disclosure.
  - New section \texttt{supp:related\_positioning} with the long
    related-work positioning table moved out of the main body to keep
    the body within the page envelope.
  - Source-trace table updated with the two human-eval rows.

### Tracking & disclosure docs
- `papers/paper_neurips/SOURCE_TRACE.md` — three additional rows:
  $n=99$ calibration with full file list, $n=100$ disagreement batch
  with explicit "labels pending" flag, and context-conditioned NLI
  artefact list. New "Honest Disclosure on Scorer Implementations"
  section spelling out the legacy-proxy vs context-conditioned
  distinction.
- `papers/paper_neurips/ULTIMATE_REVISION_PLAN.md` — pre-pass plan
  recording the repo state, action items, and items deliberately not
  done.

### Code (added to repo)
- `scripts/run_context_conditioned_nli_scoring.py` — new resumable
  context-conditioned NLI rescoring script, supports MPS / CUDA / CPU,
  no paid APIs. Used to produce the $n=600$ subset and the $n=99$
  calibration rescore. Help text in the file documents the smoke,
  $n=600$, and full-$7{,}500$ commands.
- Restored from git history into the live working tree (so the
  paper's source-trace claims map to live files):
  - `data/revision/fix_03/HUMAN_EVAL_INSTRUCTIONS.md`
  - `data/revision/fix_03/human_eval_rater_a.csv`
  - `data/revision/fix_03/human_eval_rater_b.csv`
  - `data/revision/fix_03/human_eval_adjudicated.csv`
  - `data/revision/fix_03/human_eval_n99_with_context.csv` (built from
    the adjudicated CSV by joining the three passages into one
    `context` column so the rescoring script can score it)
  - `results/revision/fix_03/human_eval_summary.csv`
  - `results/revision/fix_03/human_eval_correlations.csv`
  - `results/revision/fix_03/human_eval_label_distribution.csv`
  - `results/revision/fix_03/human_eval_verification.csv`

### New result CSVs from this pass
- `results/revision/context_conditioned_nli/per_query_smoke.csv`
- `results/revision/context_conditioned_nli/per_query_n600.csv`
- `results/revision/context_conditioned_nli/contrasts_n600.csv`
- `results/revision/context_conditioned_nli/n99_with_ctx_scores.csv`
- `results/revision/context_conditioned_nli/n99_alignment_spearmans.csv`

## Experiments / scripts run

| Step | Command | Wall-clock |
| --- | --- | --- |
| Smoke ($n=50$ rows, both NLI models, MPS) | `python3 scripts/run_context_conditioned_nli_scoring.py --input data/revision/fix_03/per_query.csv --output results/revision/context_conditioned_nli/per_query_smoke.csv --max_rows 50 --batch_size 8` | $\approx 30$ s |
| Subset ($n=600$ balanced, both models) | `python3 scripts/run_context_conditioned_nli_scoring.py --input data/revision/fix_03/per_query.csv --output results/revision/context_conditioned_nli/per_query_n600.csv --balanced_per_condition 200 --batch_size 8` | $\approx 5$ min on M4 MPS |
| $n=99$ calibration rescore | `python3 scripts/run_context_conditioned_nli_scoring.py --input data/revision/fix_03/human_eval_n99_with_context.csv --output results/revision/context_conditioned_nli/n99_with_ctx_scores.csv --batch_size 8` | $\approx 30$ s |

## Status reports per user request

- **Context-conditioned NLI status:** completed on a balanced
  $n=600$ subset and on the $n=99$ calibration items. Findings: same
  backbone NLI weights produce sign-flipped baseline$-$HCPC-v$1$
  contrasts under context-conditioned calling on the same fixed
  generations (CIs disjoint), and context-conditioning does not
  improve Spearman alignment with adjudicated labels in the
  calibration set. Full $7{,}500$-row rescoring was not attempted in
  this polish window: at MPS rates ($\sim 4$--$7$ rows/s), a full
  rescoring is feasible at $\sim 50$ minutes per model, but the
  $n=600$ subset already produces tight CIs and the disclosed result
  is treated as a focused empirical demonstration of the input-format
  axis, not a replacement for the legacy table.
- **Human-eval status:** $n=99$ two-pass adjudicated calibration is
  fully restored to the paper with verified numbers from
  `results/revision/fix_03/human_eval_*.csv`. The targeted
  $n=100$ scorer-disagreement batch is shipped prepared but
  unlabelled; no claim is made from it.
- **Updated human labels found?** No new labels were collected in
  this pass; the $n=99$ labels from the prior revision were restored
  from git history into the live working tree so the source-trace
  claims map to live files.
- **All new result paths:**
  `results/revision/context_conditioned_nli/{per_query_smoke,per_query_n600,contrasts_n600,n99_with_ctx_scores,n99_alignment_spearmans}.csv`,
  plus the restored
  `data/revision/fix_03/human_eval_*.csv` and
  `results/revision/fix_03/human_eval_*.csv` set.

## Remaining limitations (explicitly disclosed in the paper)

- **One-generator Qwen2.5 replication** — the metric-fragility
  ordering replicates compactly under one second generator
  (Qwen2.5-7B at $n=100$ per condition); broader
  generator-universal claims remain out of scope.
- **40-question long-form probe** — QASPER and MS-MARCO long-form
  results are scope-only and reported in the supplement; not broad
  long-form generalisation evidence.
- **$100$-example disagreement batch unlabelled** — labels are
  pending; we report no scorer-alignment number from this batch.
- **Context-conditioned NLI on a $600$-row subset** — the balanced
  subset shows a sign-flipped contrast with disjoint bootstrap CIs,
  but a full-$7{,}500$ rescoring would tighten the picture further.
  The supplement makes this scope explicit.
- **n=99 calibration size and overlapping CIs** — the $n=99$
  Spearman bootstrap CIs overlap, so the per-scorer ranking against
  adjudicated labels remains suggestive, not settled.

## Build status

- `papers/paper_neurips/main.pdf`: 14 pages, builds cleanly with
  `pdflatex + bibtex + pdflatex × 2`. No undefined references, no
  undefined citations.
- `papers/paper_neurips/supplement.pdf`: 12 pages, builds cleanly with
  the same sequence. No undefined references.
- Anonymous toggle (`\anonymoustrue`) preserved.

## Citations / references

- All cited works in `references.bib` resolve under `bibtex main` and
  `bibtex supplement`.
- No new citations were added in this pass beyond what was already in
  `references.bib`.

## Page count notes

- Original main paper: 12 pages.
- After this pass: 14 pages.
- Net change: $+2$ pages from the new $n=99$ calibration table and
  the context-conditioned input-format paragraph. The redundant
  seven-axis paragraph block in §4 was collapsed into one paragraph,
  and the long related-work positioning table was moved to the
  supplement, both of which partially offset the increase.

## Honest framing summary

The paper claims:

- ControlledRAG is a seven-axis disclosure standard for RAG
  faithfulness claims.
- Scorer choice and scorer input format change the reported contrast
  on fixed generations; the latter sign-flips the contrast on the
  same backbone NLI weights at the audited cell.
- The $n=99$ adjudicated calibration produces overlapping bootstrap
  CIs, so it constrains scorer-trust rather than ranking scorers.
- The targeted $100$-example scorer-disagreement batch is prepared
  with templates, codebook, and an analysis script, but is
  unlabelled at submission and is not used for any scorer-alignment
  number.
- The matched-similarity CCS test, the scaled-audit shrinkage, the
  threshold-transfer table, and the cost-aware head-to-head all
  contribute audit-axis evidence rather than method claims.

The paper does NOT claim:

- That CCS causes faithfulness, drives faithfulness, or is a
  faithfulness oracle.
- That HCPC-v$2$ dominates.
- That Qwen2.5 establishes generator-universal behaviour.
- That QASPER / MS-MARCO long-form is broad generalisation evidence.
- That the $100$-batch is completed.
- That legacy zero-shot DeBERTa / `roberta-large-mnli` proxies are
  context-grounded faithfulness scorers.
- That raw scorer contrasts on different scales are directly
  comparable causal effect sizes.
