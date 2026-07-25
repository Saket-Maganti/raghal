# Response to Reviewer d61o

## Paste-ready response

Thank you for identifying the gap between a bounded short-answer audit and
complex modern RAG. We agree: the framework’s broader applicability is a
procedural proposal, while the observed numerical effects are not established
to transfer beyond the tested cells.

For an agentic RAG system, the same disclosure structure maps naturally:
generator becomes the agent/model policy; retrieval includes search and tool
selection; context includes memory and intermediate observations;
measurement includes judge and task-success definitions; calibration uses
deployment-relevant human judgments; threshold transfer covers intervention
or abstention rules; and cost includes latency and tool calls. This is a
procedural mapping, not a claim that our measured effect sizes transfer to
agentic systems.

Operationally, define the task-level decision and endpoint, disclose all
seven practical categories, calibrate on a deployment-relevant human slice,
and stress-test reasonable choices capable of changing a sign, rank,
threshold, or deployment decision. Then report the result as stable,
conditional, or unresolved rather than compressing disagreement into a
universal score.

In a complex application, the framework succeeds only if it reveals which
conclusions remain unchanged under claim-relevant alternatives. If every
reasonable configuration selects a different system, the outcome must remain
unresolved rather than be presented as a general result. That rule makes the
procedure falsifiable at the claim level: it can withhold the conclusion when
the required stability is absent.

Existing threshold, cost, retriever, second-generator, and small long-form
cells show that the audit can be instantiated beyond one primary experiment,
but they do not constitute complex-task validation. The 40-question
long-form panel is exploratory, and the HotpotQA cost cell is not a full
multi-hop faithfulness experiment.

The evidence supports the need for the reporting procedure, while broader
complex-task effect sizes remain an explicit validation target rather than a
claim of this paper.
