# Mathematical definition audit

Status: `MATHEMATICAL_AUDIT_PASS_WITH_CLARIFICATIONS`.

Clarifications applied:

- point estimates are direct observed statistics;
- the paired system contrast is baseline minus HCPC-v1;
- the difference in contrasts is context-conditioned minus answer-only;
- the primary population is the common complete intersection of 193 pair IDs;
- human slices preserve same-row pairing and remain separate;
- seed `20260724` is used without offsets;
- bootstrap non-finite values are filtered only from CI distributions;
- the continuous score, Boolean decision, and human-alignment metrics are distinct estimands.

The missing separately named repair ZIP affects cross-ZIP provenance, not the mathematical recomputation from the accepted raw records.
