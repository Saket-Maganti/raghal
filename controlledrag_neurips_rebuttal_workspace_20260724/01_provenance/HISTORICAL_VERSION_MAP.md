# Historical Version Map

## Authority model

| Label | Tree | Role | Authority for rebuttal |
| --- | --- | --- | --- |
| SUBMITTED | `rag-hallucination-detection_main/` | Immutable artifact corresponding to the submitted reviewer package; standalone tree is clean at `59e94a5418a296acda1892e9165fd43096292f58` | Primary authority for what reviewers received and for submitted metric implementations |
| CLEANUP-SNAPSHOT | `cleanup_20260506_final_code_artifact_cleanup/prior_reviewer_artifact_snapshot/` | Complete-looking pre-cleanup reviewer snapshot | Historical candidate evidence only |
| PRE-CLEANUP | `cleanup_20260506_final_code_artifact_cleanup/root_before_cleanup/` | Broadest recovered state, including full per-query files omitted from the submitted artifact | Highest-value forensic source; never authoritative without script/config/hash trace |
| DELETED | `deleted_from_head/` | Removed or superseded material, including paper/build remnants and logs | Stale/history-only unless independently reconciled |
| MOVED | `moved_from_repo/` | Historical moved packages, paper source, notebooks, and process notes | Stale/history-only unless independently reconciled |
| INGEST-AUDIT | `audit/` | Read-only forensic reports produced before this prompt | Navigation and conflict evidence, not primary scientific output |

## Submitted identity

- Standalone submitted-artifact branch: `main`
- Standalone submitted-artifact HEAD:
  `59e94a5418a296acda1892e9165fd43096292f58`
- Anonymous reviewer ZIP SHA-256:
  `7e03cb61734f7cd9a56cd6f3ff9acecffdbc9726c835d3f8ec59dffeccce8528`
- The standalone tree is a superset of the ZIP because it also contains paper
  source/build material excluded from the anonymous artifact.

## Load-bearing conflicts

### AUPRC implementation

The submitted and cleanup versions of
`scripts/analyze_human_disagreement_labels.py` differ.

| Snapshot | Implementation | DeBERTa | second NLI | RAGAS-style | Allowed use |
| --- | --- | ---: | ---: | ---: | --- |
| Cleanup historical | manual sorted calculation | 0.761753 | 0.928433 | 0.886240 | Conflict evidence only |
| Submitted | `sklearn.metrics.average_precision_score` | 0.764813 | 0.928793 | 0.859367 | Submitted-value authority; paper rounds to 0.765/0.929/0.859 |

Never mix these values. Prompt 02 must reproduce the submitted implementation
from submitted labels/scores before marking the claim verified.

### Paper source and PDF

Paper source, supplement, bibliography, and compiled PDF differ between moved
historical material and the standalone submitted local tree. The actual venue
submission export has not been independently matched to either package. Use
the standalone source for initial extraction, but keep the associated claims
`TO_VERIFY` until submission identity is established.

### Reviewer package generations

The current anonymous reviewer ZIP and the historical “previous reviewer”
archive have different hashes and sizes. The current submitted ZIP is the
baseline. Historical packages may explain missing files but must not be used
as if reviewers received them.

## Missing full per-query inputs

The submitted artifact contains one path matching `*per_query*`:

`data/revision/fix_06/per_query_compact.csv`

The cleanup pre-cleanup tree contains 127 matching paths. Prompt 01 hashed the
highest-priority full candidates for fix 01, 02, 03, 04, 05, 06, 11, 14, and
15. Their presence does not prove their provenance. Prompt 02 must establish:

1. schema and row-count agreement;
2. generating script and configuration;
3. summary reconstruction;
4. version compatibility with submitted code;
5. whether the file predates the submitted result.

## Syntax-broken optional scripts

The following submitted optional entry points are syntactically invalid
because `from __future__ import annotations` is not at the beginning:

- `experiments/run_adaptive_chunking_ablation.py`
- `experiments/run_coherence_analysis.py`
- `experiments/run_hcpc_ablation.py`
- `experiments/run_reranker_experiment.py`

They were not repaired because the submitted artifact is immutable and Prompt
01 is an evidence-mapping stage.

## Incomplete or absent experiments

- Contradictory/conflicting-context seeds and scripts exist, but no completed
  result folder was found.
- A Together/Llama-3.3-70B fix-07 script exists without frozen fix-07 inputs
  or outputs.
- A Self-RAG run is incomplete/harness-mismatched and must not support a broad
  claim about Self-RAG.
- The long-form run is only 40 questions and is exploratory.
- The Qwen2.5 run is one model at 100 contexts per condition.
- BGE/E5 matched-pair evidence is re-encoding of fixed contexts.

## Safe version-selection rule

For what was submitted, prefer SUBMITTED. For missing row-level evidence,
start from PRE-CLEANUP, but do not cite it until Prompt 02 reconstructs the
submitted summary and validates code/config compatibility. Preserve every
conflict explicitly; do not silently reconcile.
