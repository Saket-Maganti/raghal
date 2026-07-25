# Result citation and receipt

Use the preferred response package only after professor approval and anonymous-mirror refresh.

## Audited result

On 193 common-complete baseline–HCPC-v1 pairs, the answer-only paired contrast was 3.316 percentage points (95% paired-bootstrap CI 0.466 to 6.269) and the context-conditioned contrast was 13.938 points (9.534 to 18.238). The direct observed difference in contrasts was 10.622 points (5.544 to 15.492).

On 83 typical human-labelled rows, context-conditioned scoring changed AP from 0.963 to 0.982, a direct difference of 0.0189 (95% CI 0.0044 to 0.0422; 9,822 finite replicates), and Spearman correlation from 0.118 to 0.251, a difference of 0.1330 (0.0607 to 0.2151; 9,822 finite replicates).

The separate 72-row disagreement-targeted diagnostic showed the same direction: AP difference 0.0657 (0.0163 to 0.1193; 10,000 finite replicates) and Spearman difference 0.2463 (0.0234 to 0.5063; 9,991 finite replicates).

## Receipt

- Pinned judge: Qwen2.5-7B family, immutable revision recorded in the private run receipt.
- Requested/received/valid/invalid: 1,510 / 1,510 / 1,507 / 3.
- Invalid category: three preserved threshold inconsistencies.
- Bootstrap: paired percentile, seed 20260724, 10,000 requested replicates.
- Point estimates: direct observed estimates, not bootstrap means.
- Public source release: integration `d26b29ee810c289e44233881f78364656f3d0612`; receipt `37b3520f035e9b22ddbb606b4c5027abd88ee79a`; remote `main` verified.
- Privacy boundary: aggregate tables and compact verification code only.

## Submission boundary

This supports material scorer-input sensitivity under one pinned judge and better context-conditioned human alignment on two audited slices. It does not establish universal evaluator correctness, universal superiority, a sign reversal, or arbitrary long-form and agentic generalisation.

The separately named repair ZIP was not located, so cross-ZIP byte identity is unverified. The accepted ZIP's shard-to-merge equivalence passes. The anonymous mirror still requires refresh and visual verification. No OpenReview submission was performed.
