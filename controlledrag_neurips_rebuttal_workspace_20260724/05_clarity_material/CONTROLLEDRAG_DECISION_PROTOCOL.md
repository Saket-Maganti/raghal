# ControlledRAG Decision Protocol

## Output classes

| Class | Meaning | Allowed action |
| --- | --- | --- |
| Stable | Direction or operational conclusion survives the claim-critical tested alternatives, with uncertainty and provenance checks passing | Report as the primary bounded conclusion, naming the tested scope |
| Conditional | Conclusion changes with scorer, slice, dataset, threshold, or utility weights, or is supported only by a pilot | Report the conditions and decision trade-off; do not name a universal winner |
| Unresolved | Evidence is missing, mismatched, provenance-pending, or too weak to distinguish alternatives | Do not fill the gap with a point claim; disclose what would resolve it |

In this package, stable items include the separate human-protocol facts, the
locked sklearn AP convention, weak legacy-DeBERTa alignment on both slices,
and the answer-only nature of the legacy calls. Conditional items include the
stronger-scorer ordering, Figure 2 interpretation, threshold transfer,
Pareto status, and cost utility. Unresolved items include exact
reviewer-specific mapping, the claimed matched `p=0.011`, immutable
pre-specification timing, and universal artifact completeness.

## Operational procedure

1. **Write the decision first.** Specify the decision unit, dataset/split,
   population, positive class, and acceptable faithfulness/cost constraints.
2. **Complete all seven disclosures.** Record generator, retriever, context
   structure, scorer/input, human calibration, threshold transfer, and cost.
   Use “not measured” rather than leaving a cell implicit.
3. **Lock provenance.** Label outputs generated, rescored, re-encoded,
   imported, or aggregated; attach row counts, seeds, hashes, and versions
   where available.
4. **Choose the endpoint before ranking systems.** State scorer direction,
   aggregation, threshold, and human label mapping. Do not compare native
   scorer magnitudes as though they share a scale.
5. **Calibrate on the deployment-relevant slice.** Use independent
   pre-adjudication labels for agreement and adjudicated labels for final
   scorer alignment. Keep differently sampled or differently labeled slices
   separate.
6. **Stress-test claim-critical axes.** At minimum, vary a reasonable
   alternative whenever it can change a sign, rank, threshold decision, or
   deployment choice. Otherwise narrow the claim.
7. **Propagate uncertainty.** Use paired resampling for paired contrasts and
   report point estimates with intervals; label point-estimate-only analyses.
8. **Classify the result.** Mark each finding stable, conditional, or
   unresolved and draft only at that strength.
9. **Apply the Pareto rule.** Remove dominated candidates before applying a
   scalar utility. Never call frontier membership statistical dominance.
10. **Document the decision.** Record the selected configuration, rejected
    alternatives, assumptions, and the monitoring trigger for re-evaluation.

## Pareto decision rule

For a deployment cell, define objectives before examining winners: maximize
faithfulness and minimize latency, indexing time, and any additional
predeclared burden. System A dominates B only when A is no worse on every
objective and strictly better on at least one. Discard dominated candidates.
If multiple systems remain, do not manufacture a universal ranking:

- choose explicit deployment weights or constraints;
- amortize one-time costs at a declared query volume;
- test plausible weight/volume ranges;
- select a system only if it remains acceptable under those ranges; and
- otherwise report the set of frontier options and the condition under which
  each is preferred.

For the audited fixed outputs, this rule leaves only CRAG on the HotpotQA
point-estimate frontier. On SQuAD it leaves CRAG, HCPC-v2, and RAPTOR-2L, so
the choice depends on query volume and time penalty. This is a two-dataset,
hardware-specific sensitivity, not a general winner declaration.

## Minimal practitioner record

> Decision: [task and population]. Configuration: [seven-axis entries].
> Endpoint: [metric, input, direction, threshold]. Calibration:
> [slice/protocol]. Robustness class: [stable/conditional/unresolved]. Pareto
> set: [systems]. Selected option and assumptions: [choice]. Re-evaluate when:
> [dataset/model/scorer/cost threshold changes].
