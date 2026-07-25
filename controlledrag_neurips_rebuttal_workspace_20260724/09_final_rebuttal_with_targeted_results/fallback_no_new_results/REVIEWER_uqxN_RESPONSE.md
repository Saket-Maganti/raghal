# Response to Reviewer uqxN

## Paste-ready response

Thank you for focusing on modern judges, implementation burden, and
deployment decisions. ControlledRAG applies procedurally to an LLM judge or
task-specific reward model because its identity, version, inputs, scale,
aggregation, threshold, and human calibration become explicit audit choices.
We have not empirically validated those judge families: the optional modern
judge was prepared but not executed, with zero real rows scored.

The seven categories are practical, non-unique, and non-exhaustive, and they
do not require a full factorial experiment. **Disclosure tier:** report all
seven, including “not varied” or “not measured.” **Stress-test tier:**
evaluate only reasonable alternatives capable of changing a sign, ranking,
threshold decision, or deployment choice.

**ControlledRAG in practice:** disclose all seven categories; identify
alternatives capable of changing the claim; calibrate on a
deployment-relevant human slice; stress-test only those claim-critical
alternatives; and report the conclusion as stable, conditional, or
unresolved. This is the operational answer when reasonable configurations
conflict: disagreement identifies the assumptions on which the conclusion
depends instead of being averaged away as noise.

For accuracy/robustness/cost selection, use a Pareto-first rule. Remove
systems dominated on both quality and cost, apply deployment-specific latency,
indexing, query-volume, or quality constraints to the remaining systems, and
report a conditional Pareto set when reasonable settings disagree. The
two-dataset cost audit illustrates this decision process with
hardware-specific point estimates; it does not establish a universal
economic ranking.

ControlledRAG therefore preserves full disclosure while keeping experimental
burden proportional to the strength of the claim.
