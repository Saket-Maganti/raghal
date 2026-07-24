# Response to Reviewer uqxN

## Recommended Version A — paste-ready

Thank you for recognizing the value of the audit, reusable artifacts, scorer
input-format result, and explicit cost dimension. We agree that the three
questions you raise define the framework’s practical boundary.

**Modern judges and reward models.** We have not established that the observed
numerical effects transfer to current LLM judges or task-specific reward
models, and we state this directly. The protocol is scorer-agnostic in
the limited procedural sense that any scorer must disclose its identity,
version, inputs, scale, aggregation, threshold, and human calibration. That
does not make our existing experiments a validation of untested judge
families.

**Seven axes and overhead.** We clarify that seven is a practical minimum
for this audit, not a unique or exhaustive taxonomy. Authors should disclose
all seven entries, using “not varied” or “not measured” when appropriate, but
need not run a full factorial grid. Stress testing is required only for a
reasonable alternative that could change the claim’s sign, ranking, threshold
decision, or deployment choice. This preserves diagnostic value while keeping
the burden proportional to the claim.

**Conflicting outcomes and deployment choice.** Our operational rule is to
define the deployment endpoint and constraints first; calibrate scorers
on a relevant human slice; vary claim-critical choices; then classify the
result as stable, conditional, or unresolved. For cost-sensitive selection,
remove point-estimate-dominated systems before applying explicit latency,
indexing, or query-volume constraints. If plausible settings select different
systems, report the conditional Pareto set rather than manufacture one global
winner. Our two-dataset cost audit illustrates this procedure but is not a
universal economic ranking.

## Version B — optional insertion template, not for current use

If a separately authorized modern-judge run later passes every frozen-sample,
provenance, routing, and validity gate, an additional fixed-output result may
be inserted with the immutable model/revision, sample size, complete-pair
count, paired estimate, and interval. No such result exists now, so Version A
is the complete recommended response.
