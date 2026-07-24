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
4. `MISSING_FULL_PER_QUERY_SUBMITTED`: the submitted artifact includes only
   one `*per_query*` file, while full load-bearing inputs exist only in
   recovered cleanup material and require provenance validation.
5. `AUPRC_IMPLEMENTATION_CONFLICT`: cleanup and submitted snapshots use
   different AUPRC implementations and produce different values.
6. `OPTIONAL_SCRIPTS_SYNTAX_BROKEN`: four submitted experiment entry points
   place a future import after executable content:
   `run_adaptive_chunking_ablation.py`, `run_coherence_analysis.py`,
   `run_hcpc_ablation.py`, and `run_reranker_experiment.py`.
7. `MISSING_ADVERSARIAL_RESULTS`: contradiction seeds/scripts exist, but no
   completed conflicting-evidence experiment output was located.
8. `SOURCE_TRACE_OVERSTATEMENT`: the supplement says every numerical claim
   has per-query/source support, but most full per-query inputs are absent from
   the submitted artifact.

## Non-blocking structural discrepancy

The actual Git root is nested under the diagrammed ingest directory. This was
resolved without moving or initializing repositories.

## Required user-provided input for exact review mapping

Provide a confidential local export or screenshots of the five reviews and
the AC/meta-review. If the current Git destination remains public, the export
will be used only to create sanitized paraphrases; verbatim text will not be
committed.
