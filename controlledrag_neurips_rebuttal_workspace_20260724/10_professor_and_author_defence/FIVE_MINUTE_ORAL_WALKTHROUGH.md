# Five-minute oral walkthrough

**Minute 1: contribution.** ControlledRAG is a minimum reporting and audit framework for RAG faithfulness claims. It asks authors to disclose seven practical categories and stress-test alternatives that could change the claim.

**Minute 2: submitted evidence.** The controlled audit showed scaling collapse, a null matched-context result, fixed-output scorer and input sensitivity, slice-dependent human calibration, weak threshold transfer, and quality-cost trade-offs. The evidence is strongest for short-answer RAG.

**Minute 3: new result.** A pinned Qwen2.5-7B judge scored 1,510 fixed-output requests. The answer-only system contrast is 3.32; with context it is 13.94. Their difference is 10.62 points, CI [5.54, 15.49]. Same ordering, materially different magnitude.

**Minute 4: human check and integrity.** Context conditioning improves AP and Spearman on 83 typical rows and a separate 72-row diagnostic slice. Three outputs violate the frozen threshold rule and remain invalid. No result was repaired, imputed, or pooled.

**Minute 5: action.** Authors disclose relevant categories, calibrate where possible, and mark claims Stable, Conditional, or Unresolved. The camera-ready will simplify Figure 2, add an experiment map and metric definitions, narrow scope, and document the artifact.
