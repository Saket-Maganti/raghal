# Legacy Human-Evaluation Files

## Authoritative submitted inputs

| Slice | File | Use |
| --- | --- | --- |
| `n=99` | `rag-hallucination-detection_main/human_eval_final/n99_calibration/human_eval_adjudicated.csv` | authoritative labels and row content |
| `n=99` | `.../human_eval_correlations.csv` | submitted point estimates |
| `n=99` | `.../bootstrap_correlation_cis.csv` | submitted correlation intervals |
| `n=100` | `rag-hallucination-detection_main/human_eval_final/n100_disagreement/annotation_batch_disagreement_100.csv` | authoritative labels, scores, and row content |
| `n=100` | `.../human_disagreement_correlations.csv` | submitted correlation estimates |
| `n=100` | `.../human_disagreement_auroc_auprc.csv` | submitted locked binary estimates |
| `n=100` | `.../human_disagreement_bootstrap_cis.csv` | submitted intervals |

Ellipses above retain the same slice directory; no path points outside the
four read-only source trees or rebuttal workspace.

## Provenance-approved recovered input

`cleanup_20260506_final_code_artifact_cleanup/root_before_cleanup/data/revision/fix_03/human_eval_template.jsonl`
contains the fixed `n=99` scorer values. Its 99 unique IDs match the submitted
adjudication file exactly, and its scorer values match the recovered
7,500-row fixed table at those IDs. It is used only because the submitted
adjudication CSV omits scorer columns.

## Historical or superseded material

- Historical `disagreement_alignment_n100.csv` AUPRC values
  `0.761753 / 0.928433 / 0.886240` are superseded and forbidden.
- Pre-annotation templates are not evidence of completed human labels.
- Rater-only and adjudication-template files may document process, but final
  alignment must use the complete adjudicated files.
- The `n=99` and `n=100` directories are not interchangeable replicas.

All hashes used by Prompt 03 are in
`03_existing_analyses/results/input_manifest.csv`.
