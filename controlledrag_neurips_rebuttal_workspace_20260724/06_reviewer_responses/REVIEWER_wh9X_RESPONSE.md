# Response to Reviewer wh9X

## Paste-ready response

**Metrics.** The two historical NLI metrics score the answer without
retrieved context. The third scorer evaluates question, context, and answer
jointly and is a custom RAGAS-style judge, not the official `ragas` package.
Human alignment uses average precision with faithful answers as the positive
class.

**Figure 2.** The answers do not change; only the information given to the
scorer changes, and the reported system comparison reverses. For DeBERTa,
baseline minus HCPC-v1 changes from `+0.017` to `-0.279`; the second NLI
backbone shows the same directional reversal. The figure demonstrates
fixed-output scorer-input sensitivity, not fresh generation or universal
correctness.

**Why seven categories.** Each category is included because leaving it
unspecified permits a reasonable alternative choice to change the conclusion
or deployment decision. Generator means the answer process. Retrieval means
the evidence surface. Context means the evidence shown. Scorer means the
measurement. Human calibration means the interpretation. Threshold transfer
means the operational classification. Cost means the deployment choice.
These are practical, non-unique, and non-exhaustive categories. Authors
disclose all seven but stress-test only alternatives that can change the
claim; a seven-dimensional factorial experiment is not required.

**Conflicting sources.** Cattan et al., “DRAGged into Conflicts: Detecting
and Addressing Conflicting Sources in Search-Augmented LLMs,”
arXiv:2506.08500, 2025, studies contradiction among retrieved sources. Our
fixed-output result concerns scorer disagreement. These are different
phenomena, and no contradictory-context experiment was completed.

The camera-ready will use this order: motivating decision example, claim
boundary, seven-category reporting contract, plain metric definitions,
experiment map, strongest controlled audits, bounded probes, practitioner
protocol, and limitations. These changes make the inclusion criterion,
metrics, Figure 2, and relation to contradictory-source work explicit before
the experimental details.
