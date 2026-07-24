# Do Not Use Stale Values

The following values or phrasings are quarantined from all proposed rebuttal
text.

| Quarantined item | Reason | Safe replacement |
| --- | --- | --- |
| RAGAS-style AUPRC `0.886240` | Superseded historical implementation | `0.859367` from submitted `sklearn.metrics.average_precision_score` |
| DeBERTa/second-NLI AUPRC `0.761753 / 0.928433` | Same superseded implementation | `0.764813 / 0.928793` |
| Matched hallucination McNemar `p=0.011` | Not reproduced by standard exact or asymptotic conventions | Exact two-sided `p=0.013531`, or omit p; state convention if retained |
| Span-presence McNemar `p=0.011` | Same 9-versus-24 discordance and same mismatch | Exact two-sided `p=0.013531`, or omit p |
| “Per-query CSVs for every audited cell” | Contradicted by submitted artifact inventory | Name the specific shipped files and separately identify recovered evidence |
| “Pre-registered on 2026-04-26” | Historical internal log exists, but no immutable pre-result submitted Git commit was found | Omit; if necessary, say “internally pre-specified” with an explicit provenance limitation |
| Compensation or IRB assertions | Not included in author-confirmed facts for this workflow | Omit until explicitly confirmed |
| Re-encoding as fresh retriever replication | Fix 13 matched panel re-encodes fixed contexts | “Fixed-context re-encoding diagnostic” |
| Context-conditioned NLI as universally correct | Rescoring changes sign but remains scorer-dependent | “Calling convention materially changes this fixed-row contrast” |
| Pooled `n=99 + n=100` human result | Different sampling and label schemas; zero ID overlap | Report the slices separately |
| Historical `n=30` and scaled `n=2,500/condition` as protocol-equivalent | Sampling protocols differ | Present the historical result only as a non-comparable pilot |

Any draft containing a quarantined item fails the Prompt 02 P0 gate.
