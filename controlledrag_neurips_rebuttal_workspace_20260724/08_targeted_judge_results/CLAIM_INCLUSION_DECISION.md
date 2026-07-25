# Claim inclusion decision

| Claim | Decision | Reason |
| --- | --- | --- |
| a pinned contemporary open-weight judge shows material scorer-input sensitivity | SUPPORTED_WITH_SCOPE | 10.622-point difference in contrasts; CI excludes zero |
| both interfaces preserve the same system ordering on 193 pairs | SUPPORTED | both paired contrasts are positive |
| contrast increases from 3.316 to 13.938 points with context | SUPPORTED | direct observed estimates |
| context-conditioned alignment is higher on 83 typical rows | SUPPORTED_WITH_SCOPE | AP and Spearman differences are positive |
| 72-row diagnostic shows the same direction | SUPPORTED_WITH_SCOPE | separate diagnostic AP and Spearman differences are positive |
| strong inclusion gate passes | SUPPORTED | 99.801% valid, complete keys, low differential missingness |
| three invalid outputs were preserved | SUPPORTED | independent strict parse confirms three threshold inconsistencies |
| modern judge produces a sign reversal | FORBIDDEN | both contrasts have the same sign |
| context conditioning is universally correct or superior | FORBIDDEN | two bounded slices and one pinned judge cannot support universality |
| experiment proves ground-truth correctness | NOT_SUPPORTED | it measures scorer behavior and bounded human alignment |
| 72-row slice is confirmatory | FORBIDDEN | it is disagreement-targeted and diagnostic |
| experiment is broad human validation | NOT_SUPPORTED | two small audited slices |
| all 194 pairs were analyzed | FORBIDDEN | primary complete population is 193 |
| all 1,510 outputs were valid | FORBIDDEN | three remain invalid |
| result generalizes to arbitrary long-form or agentic systems | NOT_SUPPORTED | audit is centered on short-answer RAG |
| first corrupted run may be combined with the repair run | FORBIDDEN | no pooling across runs |
| invalid outputs may be manually recoded | FORBIDDEN | frozen strict rule |

Approved bounded wording:

> On 193 fixed-output baseline-HCPC-v1 pairs, a pinned Qwen2.5-7B judge preserved the system ordering under both interfaces, but exposing retrieved context increased the measured contrast from 3.32 to 13.94 points, a 10.62-point shift. On a separate 83-row determinate human-labelled slice, context-conditioned scoring improved AP from 0.963 to 0.982 and Spearman correlation from 0.118 to 0.251. A separately analysed 72-row disagreement-targeted diagnostic slice showed the same direction.

> This supports scorer-input sensitivity and better context-conditioned human alignment on these audited slices; it does not establish universal superiority or guarantee a sign reversal.
