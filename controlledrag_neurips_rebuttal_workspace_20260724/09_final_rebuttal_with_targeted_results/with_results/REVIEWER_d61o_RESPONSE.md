Thank you for separating the paper's important evaluation question from its narrow short-answer evidence. We agree that the numerical results should not be projected onto arbitrary long-form or agentic RAG.

**Contemporary empirical extension.** We ran a pinned Qwen2.5-7B-Instruct judge on 1,510 fixed-output requests. On the same 193 complete baseline-HCPC-v1 pairs, the answer-only contrast is **3.32 points** and the context-conditioned contrast is **13.94 points**. Their paired difference is **10.62 points**, 95% CI **[5.54, 15.49]**.

This current open-weight judge preserves the system ordering but changes the measured effect magnitude materially. It extends the submitted fixed-output NLI result without regenerating answers or changing the panel.

Same-row human calibration gives bounded evidence about evaluator correctness. On 83 typical determinate rows, context conditioning raises AP from **0.963 to 0.982** and Spearman from **0.118 to 0.251**. A separate 72-row disagreement-targeted diagnostic slice shows the same direction. These are small audited slices, not broad human validation.

**Scope.** The strongest evidence remains controlled short-answer QA with local 7B-class models. The 40-question long-form panel is exploratory. We make no numerical claim about agentic systems, proprietary frontier models, or contradictory retrieved evidence.

ControlledRAG's broader proposal is procedural. In a more complex system, authors should state the task-level decision, disclose the relevant generator/retrieval/context/scorer/calibration/threshold/cost choices, stress-test claim-critical alternatives, and classify the result as Stable, Conditional, or Unresolved. If plausible configurations select different systems and calibration cannot adjudicate them, the claim remains Unresolved.

We will make this boundary explicit in the abstract, evidence map, and limitations, and place confirmatory evidence above supporting and exploratory probes.
