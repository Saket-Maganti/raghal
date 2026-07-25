Thank you for saying plainly that the current organization makes the work look like a position paper and the codebase hard to assess. The empirical contribution is a controlled self-audit of RAG-faithfulness evaluation, but the paper and artifact did not expose that structure well enough.

**What was actually run.**

| Audit question | Panel | Population | Evidence grade |
| --- | --- | ---: | --- |
| does the scaled retrieval effect persist? | SQuAD/Mistral | 2,500 rows per condition | confirmatory controlled audit |
| does context structure matter at matched similarity? | matched SQuAD | 200 pairs | confirmatory controlled audit |
| can scorer choice change fixed-output conclusions? | fixed Mistral generations | 7,500 rows | confirmatory controlled audit |
| can scorer input change fixed-output conclusions? | balanced panel | 600 rows; 194 primary pairs | confirmatory controlled audit |
| do thresholds transfer? | five datasets x five thresholds | 25 cells | supporting |
| do quality-only rankings survive cost? | SQuAD and HotpotQA | 3 systems x 200 rows per dataset | supporting |
| does a contemporary judge show input sensitivity? | pinned Qwen2.5-7B | 1,510 requests; 193 complete pairs | supporting rebuttal experiment |
| do the two interfaces align differently with humans? | typical and targeted slices | 83 and 72 rows, separate | supporting / diagnostic |
| does the result generalize to long form? | QASPER/MS-MARCO | 40 questions | exploratory |

The new judge result is concrete: the baseline-HCPC-v1 contrast is **3.32** under answer-only scoring and **13.94** with context. The paired difference is **10.62 points**, 95% CI **[5.54, 15.49]**. Same ordering, materially different magnitude.

**Why this is more than a position paper.** The framework is demonstrated through fixed-output interventions, paired estimands, human calibration, threshold transfer, and cost analysis. Its output is an auditable decision protocol, not a new retriever or benchmark.

We also rebuilt the source artifact. The reviewer path now begins with one evidence table and one CPU-safe validation command. Every headline claim maps to an aggregate table, canonical estimator, regression test, and receipt. The release validator checks imports, 19 mathematical contracts, aggregate populations, checksums, privacy, identity, local paths, stale values, README commands, and claim links.

Private questions, contexts, answers, row identifiers, human annotation rows, and raw judge outputs are withheld. The public branch contains aggregate evidence only. Historical code remains recoverable through backup refs rather than cluttering the reviewer path.

We will add the experiment map above to the camera-ready and label each cell confirmatory, supporting, diagnostic, exploratory, or not tested.
