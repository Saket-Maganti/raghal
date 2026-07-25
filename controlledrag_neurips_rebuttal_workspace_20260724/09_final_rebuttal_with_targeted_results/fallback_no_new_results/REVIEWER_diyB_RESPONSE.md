# Response to Reviewer diyB

## Paste-ready response

The empirical contribution is a controlled self-audit of RAG-faithfulness
evaluation rather than a new model or metric. The position-paper
characterization is understandable because the current organization obscured
the experiment inventory, dataset roles, and canonical artifact path.

**Primary controlled audits:** a 200-pair matched-context study; a fixed
7,500-row scorer comparison, with 2,500 rows per condition and seeds 41–45;
and a 600-row fixed-output scorer-input analysis, with 194 complete
baseline/HCPC-v1 pairs per context-conditioned backbone.

**Human and operational audits:** separate `n=99` typical and `n=100`
disagreement-targeted human slices; a five-dataset, five-threshold transfer
grid; and a two-dataset cost comparison with three systems × 200 rows per
dataset.

**Bounded breadth probes:** retriever diagnostics, including a 720-row pilot
and separate 1,200-row fixed-context re-encoding panel; one 300-row
Qwen2.5-7B probe; and a 40-question long-form panel.

The experiments answer distinct audit questions rather than form one
homogeneous benchmark: matched-context rows isolate context construction;
fixed outputs isolate scorer choice; human slices test alignment; threshold
grids test portability; and cost cells test whether quality-only rankings
survive deployment constraints. The paper does not introduce a new dataset;
existing datasets provide controlled cells for auditing RAG-faithfulness
claims.

The canonical reviewer path is the root README, the lightweight analysis
entry point, and the experiment map. Historical and recovered trees are
evidence sources, not part of the canonical execution path. The experiment
map will state dataset/split, sample size, generator, retriever/context,
scorer input, seed status, output origin, uncertainty, and evidence grade for
each cell.

The artifact map distinguishes row-reconstructable from summary-verifiable
results and labels outputs as generated, rescored, re-encoded, imported, or
aggregated. Where complete per-query rows were not included in the reviewer
artifact, we state that limitation rather than imply universal row-level
coverage.

This organization makes the empirical audit and its provenance directly
assessable without overstating its breadth or artifact completeness.
