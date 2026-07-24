# Meta-Review Response Map

## Provenance warning

No exact AC/meta-review artifact was found. The rows below map the 14 sanitized
concern clusters recovered from the pre-existing audit. They are preparation
material, not claims about what the AC wrote.

| ID | Faithfully paraphrased concern cluster | Category | Strongest current evidence | Clarification suffices? | Existing-output analysis helps? | Optional judge helps? | Overclaiming risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | Empirical evidence is narrow relative to broad RAG implications. | Scope/generalization | Explicit main-paper limitations plus bounded Qwen/retriever/long-form probes. | Partly; scope must be narrowed. | Yes, via coverage/uncertainty map. | Marginally; one judge does not broaden generator/dataset coverage. | High if probes are described as broad replication. |
| M02 | Short-answer evidence may not cover multi-hop or synthesis tasks. | Dataset coverage | 40-question QASPER/MS-MARCO stress summary and HotpotQA cost cells. | Yes for limitation, not empirical expansion. | Yes after per-query provenance. | No, not without broader task data. | High if cost cells are called multi-hop validation. |
| M03 | Evaluation lacks a modern or task-specific judge. | Scorer coverage | Three executed scorers, fixed-row input-format analysis, human slices. | Partly. | Yes, to clarify what current scorers do. | Potentially, but rebuttal completeness cannot depend on it. | High if discussed frameworks are implied to have been run. |
| M04 | Evidence strength is uneven across the seven axes. | Evidence design | Discussion strength tags and filled checklist. | Yes if evidence grades and sample sizes are explicit. | Strongly; build a cell-level matrix. | Only for the scorer axis. | High if all axes are called equally established. |
| M05 | Practitioner action when scorers disagree is unclear. | Guidance | Slice-dependent human alignment and cost-aware table. | Partly. | Yes; conservative conditional decision table. | Potentially, but cannot validate a universal rule. | High if one scorer is recommended universally. |
| M06 | Metric implementation/input definitions are dense or ambiguous. | Metric clarity/integrity | Main/supplement definitions plus submitted AUPRC script/output. | Mostly. | Essential; recompute from submitted implementation. | No. | Critical if cleanup and submitted AUPRC values are mixed. |
| M07 | The choice of exactly seven axes is insufficiently justified. | Conceptual framework | Reasonable-substitution criterion and axis-to-overclaim mapping. | Mostly. | Yes; connect axes to observed sensitivities. | No. | High if seven is called unique or exhaustive. |
| M08 | Dataset and experiment cells are hard to reconstruct. | Reproducibility | Claims audit, source trace, manifest, reporting checklist. | Partly. | Essential; claim-to-cell provenance ledger. | No. | Critical if re-encoding/imported summaries are called fresh runs. |
| M09 | The codebase is chaotic or hard to execute. | Artifact quality | Clean submitted artifact, lightweight entry point, prior smoke audit. | Mostly for reviewer navigation. | No new scientific analysis. | No. | High if historical trees are presented as canonical. |
| M10 | Conflicting evidence in retrieved context is not evaluated. | Missing experiment | Contradiction seeds/scripts, but no completed output. | Yes to acknowledge absence. | Seed validation only. | Not by itself. | Critical if scorer disagreement is conflated with contradictory context. |
| M11 | Scorer input format and human calibration need clearer interpretation. | Scorer/human calibration | Same-backbone fixed-row sign flips; separate `n=99` and `n=100` slices. | Mostly. | Essential for uncertainty and trace validation. | Could extend the axis, but is optional. | Critical if context-conditioned NLI is called correct or slices are pooled. |
| M12 | Annotation provenance and wording appear inconsistent. | Human-evaluation provenance | Independent rater files, adjudication files, author-confirmed protocol. | Mostly. | Essential; verify IDs and transforms separately by slice. | No. | Critical if agreement uses adjudicated labels or slice schemas are silently merged. |
| M13 | Privacy, prompt injection, or release safety may be at risk. | Integrity/privacy | Existing safety audit and current public-repository block. | Yes. | Repeat scans only. | No. | Critical if confidential text or identities enter the public repo. |
| M14 | Missing full per-query files weaken the source trace. | Provenance/reproducibility | Submitted frozen summaries plus 127 recovered candidate per-query paths. | No; clarification must accompany actual tracing. | Highest-value Prompt 02 work. | No. | Critical if remnant existence is treated as proof of provenance. |

## Recommended response order if the actual meta-review confirms these themes

1. Metric and annotation integrity: M06, M11, M12.
2. Claim-to-source provenance: M08, M14.
3. Scope and evidence grading: M01, M02, M04.
4. Framework/guidance clarity: M05, M07.
5. Artifact navigation and safety: M09, M13.
6. Explicitly missing experiments: M03, M10.

This ordering is evidence-risk based, not reviewer-score based. Reviewer-score
prioritization remains impossible until the exact reviews are supplied.
