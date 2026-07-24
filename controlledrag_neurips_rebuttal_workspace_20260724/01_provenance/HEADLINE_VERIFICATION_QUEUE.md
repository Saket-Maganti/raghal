# Headline Verification Queue

Prompt 01 extracted claims but did not perform full numerical verification.
This queue orders Prompt 02 by rebuttal impact and scientific-integrity risk.

| Rank | Claim group | Ledger IDs | Submitted evidence | Recovered candidate | Verification action | Blocking risk |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | n=100 AUPRC/AUROC and submitted implementation | CR-035–CR-040 | Submitted labels, summary, and script | Historical conflicting script/output | Recompute from submitted adjudicated labels and scorer columns; pin sklearn behavior; compare exact/rounded values | Critical AUPRC version conflict |
| 2 | n=99/n=100 protocol separation and agreement | CR-031–CR-040 | Separate rater/adjudication files | Cleanup copies | Verify row IDs, disjointness, label schemas, missingness; compute agreement from pre-adjudication labels and alignment from adjudicated labels | Pooling or label-collapse error |
| 3 | Matched-context null and thresholded tail result | CR-006–CR-015 | fix-01 summaries | fix-01 full per-query | Reconstruct pairing, similarity/CCS gaps, mean difference, Wilcoxon, dz, bootstrap CI, McNemar, span diagnostic | Full rows absent from submitted artifact |
| 4 | Scaled audit pooled/per-seed result | CR-016–CR-023 | fix-02 summaries | fix-02 full per-query | Verify row counts, seeds, duplicates, means, Wilson CIs, paired contrasts, historical pilot non-comparability | 12.6 MB recovered file; provenance untraced |
| 5 | Fixed-generation scorer fragility | CR-024–CR-027 | fix-03 summaries | fix-03 full per-query | Verify scorer columns, fixed-row identity, raw/z/rank transforms, key collapse, correlations | Native scales/input formats differ |
| 6 | Context-conditioned NLI subset | CR-028–CR-030 | n600/n99 summaries | Candidate fixed rows in cleanup | Verify deterministic subset, 200 rows/condition, same generations/backbones, truncation, aggregation, paired bootstrap | Must remain a rescoring claim |
| 7 | Artifact/source-trace completeness | CR-059–CR-062 | trace docs and ZIP | 127 recovered per-query paths | Enumerate actual ZIP contents; map every paper table/figure to source rows and command; flag absent audit_log/protocol files | Current universal per-query assertion appears false |
| 8 | Threshold transfer | CR-041–CR-044 | fix-04 matrix and summaries | fix-04 full per-query | Rebuild per-tau recovery, selected tau, 5x5 transfer, identical-row logic, sign-changing cells | No uncertainty intervals |
| 9 | Cost-aware table | CR-045–CR-050 | fix-06 compact rows/summaries; fix-11 | full fix-06/fix-11 rows | Recompute means/CIs/rates; trace timing and indexing boundaries; compare compact vs full | Hardware/harness specificity |
| 10 | Span/control diagnostic | CR-013–CR-015 | fix-12 summaries | fix-01 rows and candidate fix-12 sources | Recreate lexical normalization, predictors, R2/AUROC and CIs | Post-hoc; small absolute R2 |
| 11 | Retriever sanity/pilot | CR-051–CR-052 | fix-13 and multi-retriever summaries | recovered per-query retriever material | Separate fixed-context re-encoding from pilot generation and verify each within-row comparison | High risk of calling re-encoding fresh generation |
| 12 | Qwen second-generator probe | CR-053–CR-054 | fix-14 summaries | fix-14 per-query + sample manifest | Verify 100/condition, generator identity, context sampling, scorer columns, correlations | One-model bounded probe |
| 13 | Long-form probe | CR-055–CR-057 | fix-15 summaries | fix-15 per-query | Verify 20+20 distinct questions, condition aggregation, definitions, contrasts | Exploratory only |
| 14 | Noise slopes | CR-058 | fix-05 summaries | fix-05 per-query | Refit slopes from fixed rows and confirm no significance claim | Point estimates only |
| 15 | Seven-axis conceptual and scope claims | CR-001–CR-005 | paper/checklist | not applicable | Check wording against evidence grades and remove uniqueness/universality implications | Overclaiming rather than arithmetic |

## Prompt 02 exit criteria

- Every critical headline claim has a reproducible row-level or explicitly
  summary-only disposition.
- Submitted and historical metric implementations remain separated.
- No numerical claim is marked verified solely because a summary file exists.
- Missing source, non-comparable protocols, and incomplete experiments remain
  explicit.
- No model, API, Hugging Face real-model, Kaggle, Colab, or local LLM run is
  executed.
