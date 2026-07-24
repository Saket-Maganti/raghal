# Response to Reviewer d61o

## Paste-ready response

Thank you for recognizing the importance of standardized RAG-faithfulness
reporting and for identifying generalizability as the central limitation. We
agree that the current experiments do not validate the observed numerical
effects in complex or agentic RAG.

We distinguish the methodological and empirical claims. The methodological
proposal is a disclosure procedure: report the generation setup, retrieval
setup, context construction, measurement rule, calibration evidence,
threshold portability, and deployment cost; identify claim-critical
alternatives; and classify the result as stable, conditional, or unresolved.
This procedure can be
instantiated for multi-hop, long-form, or agentic systems, but that
applicability claim is procedural. It does not imply that our measured effect
sizes or rankings transfer to those settings.

The numerical evidence remains bounded primarily to short-answer QA and
7B-class local generators. The available breadth is:
a five-dataset threshold grid, a HotpotQA/SQuAD cost cell, bounded retriever
diagnostics, one Qwen2.5-7B probe, and an exploratory 40-question
MS-MARCO/QASPER long-form panel. The long-form panel is too small for a broad
claim, and the HotpotQA cost cell is not a full multi-hop faithfulness
validation.

For complex applications, the concrete guidance is to define the task-level
decision and endpoint first, disclose all seven categories, calibrate on a
deployment-relevant human slice, and stress-test only choices capable of
changing the sign, rank, threshold, or deployment decision. A result that
depends on those choices should be reported conditionally rather than
aggregated into a single universal score. Broader complex-task validation
remains future work.
