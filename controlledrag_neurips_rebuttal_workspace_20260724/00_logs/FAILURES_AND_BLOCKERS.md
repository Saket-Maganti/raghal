# Failures and Blockers

## Active blockers

1. `PUSH_BLOCKED_REPOSITORY_PUBLIC`: the authenticated target repository is
   public, so no rebuttal branch may be pushed.
2. `SOURCE_MISSING_REVIEWS`: the exact five review texts and the AC/meta-review
   were not found in the available source trees, local prompt pack, or audit
   materials.
3. `SOURCE_MISSING_REVIEW_METADATA`: reviewer IDs, scores, confidence values,
   direct questions, and exact per-review concern attribution cannot be
   reconstructed without fabricating.
4. `MISSING_FULL_PER_QUERY_SUBMITTED`: the submitted artifact does not ship
   full per-query inputs for every audited cell. Prompt 02 validated selected
   recovered inputs by hash, but they must remain labeled recovered.
5. `MATCHED_MCNEMAR_P_MISMATCH`: the claimed `p=0.011` is not reproduced;
   exact two-sided `p=0.013531` is the safe replacement if the convention is
   declared.
6. `OPTIONAL_SCRIPTS_SYNTAX_BROKEN`: four submitted experiment entry points
   place a future import after executable content:
   `run_adaptive_chunking_ablation.py`, `run_coherence_analysis.py`,
   `run_hcpc_ablation.py`, and `run_reranker_experiment.py`.
7. `MISSING_ADVERSARIAL_RESULTS`: contradiction seeds/scripts exist, but no
   completed conflicting-evidence experiment output was located.
8. `SOURCE_TRACE_OVERSTATEMENT`: the supplement says every numerical claim
   has per-query/source support, but most full per-query inputs are absent from
   the submitted artifact.
9. `PRESPEC_TIMESTAMP_NOT_IMMUTABLE`: a historical internal log states
   `2026-04-26`, but no pre-result submitted Git commit was found.

## Resolved in Prompt 02

- `AUPRC_IMPLEMENTATION_CONFLICT`: the submitted convention is locked to
  `sklearn.metrics.average_precision_score`; historical values are
  superseded.
- Full recovered inputs for the headline numerical panels were mapped,
  hashed, and independently recomputed without altering source folders.

## Non-blocking validation-tool failure

Artifact-tool CSV inspection could not load because macOS rejected its
bundled native module's code signature. Python and shell CSV/schema checks
were used instead. This does not affect the fixed-data calculations.

## Non-blocking structural discrepancy

The actual Git root is nested under the diagrammed ingest directory. This was
resolved without moving or initializing repositories.

## Required user-provided input for exact review mapping

Provide a confidential local export or screenshots of the five reviews and
the AC/meta-review. If the current Git destination remains public, the export
will be used only to create sanitized paraphrases; verbatim text will not be
committed.
