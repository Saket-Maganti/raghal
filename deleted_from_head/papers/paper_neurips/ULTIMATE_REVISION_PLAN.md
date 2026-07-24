# Ultimate Revision Plan — NeurIPS ControlledRAG Paper

This plan documents the state of the repo, the audit findings, and the
revision actions taken in the senior-reviewer polish pass that produced
this version of `papers/paper_neurips/`.

## 1. Repo state at start of pass

- Working branch: `neurips-controlledrag-review-fixes` (main repo). A
  worktree on `claude/epic-jones-8038ff` was used for safety.
- `papers/paper_neurips/main.tex` compiles to a 12-ish page review-version
  PDF. Two text bugs in the abstract were live:
  1. The Qwen2.5 sentence was missing the third raw-contrast value
     (the RAGAS-style judge contrast `0.134`) and the next sentence was
     fused into mid-clause.
  2. The "scaled audit" sentence dropped its lead-in (`At scale, the
     SQuAD/Mistral …`), so the paragraph started with a bare phrase.
- `papers/paper_neurips/sections/controlledrag_main.tex` had drifted:
  Section 8 had been weakened from a completed `n=99` two-pass
  calibration into a "100-example disagreement protocol" stub, even
  though the verified `n=99` numbers (raw agreement `0.919`, Cohen's
  $\kappa$ `0.774`, Spearman `0.103 / 0.394 / 0.549`) are still listed
  in `SOURCE_TRACE.md` and verified by `git show 341fadcd:results/...`.
- DeBERTa and `roberta-large-mnli` were already correctly named as
  legacy zero-shot label proxies in
  `controlledrag_main.tex` and `setup.tex`. The supplement scorer
  section (`supp:scorer_standardized`) also explicitly states the
  retrieved context is not consumed by those two proxies. This
  disclosure is honest and was preserved.

## 2. Discovered result files (relevant)

| Artifact | Path | Status |
| --- | --- | --- |
| `n=99` rater A annotations | `data/revision/fix_03/human_eval_rater_a.csv` (in git history) | 99 rows, label + notes |
| `n=99` rater B annotations | `data/revision/fix_03/human_eval_rater_b.csv` (in git history) | 99 rows, label + notes |
| `n=99` adjudicated labels | `data/revision/fix_03/human_eval_adjudicated.csv` | 99 rows |
| `n=99` agreement summary | `archive/legacy_papers/neuripsnewpaper/source_tables/human_eval_summary.csv` (and `human_eval_correlations.csv`, `human_eval_label_distribution.csv`) | Verified: $\kappa$ `0.773779`, raw agreement `0.919192`, Spearman `0.103 / 0.393969 / 0.548699` |
| Mistral 7,500 fixed-generation per-query | `data/revision/fix_03/per_query.csv` | All three scorer columns + retrieved context |
| Mistral standardized contrasts | `results/revision/fix_03/standardized_scorer_fragility.csv` | z and rank contrasts |
| Qwen2.5 replication | `results/revision/fix_14/` | $n=100$ per condition, raw `0.015 / 0.046 / 0.134` |
| Matched-context pairs (HIGH/LOW CCS) | `results/revision/fix_01/` and `data/revision/fix_01/matched_pairs.csv` | $n=200$ pairs |
| Targeted 100-example disagreement batch (unlabeled) | `results/human_disagreement_expansion/annotation_batch_disagreement_100.csv` and rater/adjudication templates | **Unlabeled. Not used for paper claims.** |

## 3. Action plan executed

1. **Fixed the abstract.** Restored the Qwen2.5 third value (`0.134`)
   and the scaled-audit sentence opener (`At scale, the SQuAD/Mistral
   …`). Tightened to a single-paragraph block under the NeurIPS limit.
2. **Restored Section 8.1: completed `n=99` annotation calibration.**
   Reinstated the verified Cohen's $\kappa$ and Spearman correlations
   from `archive/legacy_papers/neuripsnewpaper/source_tables/human_*`,
   noted that bootstrap CIs overlap so the scorer ranking is suggestive
   (the SOURCE_TRACE flags this explicitly), and made it clear this is
   calibration, not a settled scorer ranking.
3. **Added Section 8.2: targeted 100-example disagreement batch.**
   Kept the existing batch-construction language but explicitly framed
   it as **prepared, infrastructure complete, labels pending** because
   no completed independent labels exist in
   `results/human_disagreement_expansion/`. This is honest disclosure
   and matches `missing_human_labels_report.md`.
4. **Did not fabricate context-conditioned NLI rescoring.** A full
   rescoring pass on 7,500 rows is not feasible inside the polish
   window without GPU access. The DeBERTa and `roberta-large-mnli`
   rows are already labelled as **legacy zero-shot label proxies** in
   `controlledrag_main.tex` (Section 3) and the supplement
   (`supp:scorer_standardized`). The metric-fragility table is framed
   as a scorer-input-formatting audit axis. We strengthened the wording
   so that no row is ever called a "faithfulness scorer" without that
   qualifier.
5. **Updated SOURCE_TRACE.md** to reflect the restored Section 8.1
   numbers and to explicitly point at the unlabeled
   `results/human_disagreement_expansion/` artifact for Section 8.2.
6. **Updated supplement Section 10** to mirror the main paper:
   `supp:human_calibration` for the completed `n=99` calibration and
   `supp:human_disagreement` for the targeted 100-example batch.
7. **Limitations** were tightened so the calibration scope and the
   pending status of the 100-batch are stated once, clearly, and not
   repeated defensively.
8. Built `main.pdf` and `supplement.pdf`; both compile cleanly with
   `pdflatex + bibtex + pdflatex × 2`.

## 4. Items deliberately NOT done

- **Did not fabricate human labels for the 100-batch.** Doing so would
  violate the project's no-fabrication rule and the
  ControlledRAG honesty contract. The batch ships unlabeled with
  templates and codebook so that an independent annotator can complete
  it post-acceptance.
- **Did not run context-conditioned DeBERTa / `roberta-large-mnli`
  rescoring.** A defensible run would need either (a) a CUDA GPU not
  available in this session, or (b) several hours of M4-only compute,
  which is outside the polish window. Disclosure of the legacy
  zero-shot proxy nature was kept explicit, and the standardized
  z-contrast / rank-contrast columns remain the load-bearing
  scorer-fragility evidence.
- **Did not expand QASPER / MS-MARCO**, run new Llama-3 generations,
  or add new ablations. Scope of the polish is honesty and clarity, not
  new experiments.

## 5. Final claim boundary (post-polish)

What the paper now says (and only says):

- ControlledRAG is a seven-axis disclosure standard for RAG
  faithfulness claims.
- On the audited cells, fixed-generation scorer choice changes the raw
  reported contrast across DeBERTa proxy / `roberta-large-mnli` proxy /
  RAGAS-style judge from `0.011` to `0.140`, with the same ordering
  preserved on a compact Qwen2.5 replication.
- A two-pass annotation calibration on $n=99$ adjudicated examples
  yields Cohen's $\kappa = 0.774$ between the two annotation passes
  and Spearman correlations against the adjudicated label of `0.103`,
  `0.394`, `0.549` for the DeBERTa proxy, the `roberta-large-mnli`
  proxy, and the RAGAS-style judge respectively. Bootstrap CIs on
  these correlations overlap, so the scorer ranking is **suggestive
  only**.
- A targeted 100-example scorer-disagreement batch is prepared with
  templates, codebook, and an analysis script, but **labels are
  pending and no scorer-alignment claim is made from this batch**.
- The matched-similarity CCS test on $n=200$ pairs is null
  (`-0.002`, $p = 0.628$, 95% CI `[-0.022, 0.017]`).
- The scaled audit shrinks the original headline to
  `0.661 / 0.650 / 0.661` over $n=2{,}500$ examples per condition.
- Threshold transfer is uneven and includes sign-changing cells.
- A cost-aware head-to-head produces no dominating system across
  CRAG / HCPC-v2 / RAPTOR-2L.

What the paper does NOT claim:

- That CCS causes faithfulness, drives faithfulness, or is a
  faithfulness oracle.
- That HCPC-v2 dominates.
- That Qwen2.5 replication establishes generator-universal behaviour.
- That the long-form QASPER / MS-MARCO probe is broad generalisation
  evidence.
- That the 100-example disagreement batch is completed.
- That legacy zero-shot DeBERTa / `roberta-large-mnli` proxies are
  context-grounded faithfulness scorers.
- That raw scorer contrasts on different scales are directly comparable
  causal effect sizes.

## 6. Build status

- `main.pdf` builds cleanly with `pdflatex main && bibtex main &&
  pdflatex main && pdflatex main`.
- `supplement.pdf` builds cleanly with the same sequence on
  `supplement.tex`.
- No undefined references, no undefined citations.
- Anonymous toggle (`\anonymoustrue`) preserved.
