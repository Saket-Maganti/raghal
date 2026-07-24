# What Not to Claim

This file is the final Prompt 6 claim-denial list.

1. Do not use stale average-precision/AUPRC values. The locked separate
   `n=100` sklearn AP values are `0.764813 / 0.928793 / 0.859367`.
2. Do not use the unreproduced matched binary `p=0.011`. If a p-value is
   essential, use exact two-sided `p=0.013531` only with its convention;
   omission is safer.
3. Do not pool the `n=99` typical and `n=100` disagreement-targeted human
   slices, combine their schemas, or treat either targeted panel as population
   prevalence.
4. Do not use adjudicated labels to compute inter-rater agreement. Agreement
   uses pre-adjudication labels; scorer alignment uses adjudicated labels.
5. Do not add unconfirmed rater qualifications, compensation, IRB status,
   LLM assistance, adjudicator identity, or the external rater’s identity.
6. Do not call the legacy NLI columns context-conditioned entailment or ground
   truth. They are answer-only zero-shot label proxies.
7. Do not call the custom scorer official RAGAS. It is a RAGAS-style judge.
8. Do not claim a verified same-row human comparison between answer-only and
   context-conditioned NLI; none exists.
9. Do not claim context-conditioned NLI is universally correct.
10. Do not call fixed-output rescoring or fixed-context re-encoding fresh
    retrieval or generation.
11. Do not call the seven categories mathematically unique, formally
    exhaustive, or equally validated.
12. Do not broaden the Qwen, retriever, long-form, threshold, cost, or
    multi-retriever probes into broad empirical validation.
13. Do not present the 40-question long-form panel as complex-task
    validation.
14. Do not present HotpotQA cost rows as a full multi-hop faithfulness
    experiment.
15. Do not call point-estimate Pareto membership statistical dominance or
    claim a universal cost winner.
16. Do not claim universal threshold transfer.
17. Do not claim any modern-judge result. The exact status is
    `PROMPT_05_REPAIRED_PREPARED_NOT_EXECUTED`; real rows scored: zero.
18. Do not use the optional Version B template unless a separately authorized
    run passes every frozen-sample, provenance, routing, privacy, and validity
    gate.
19. Do not conflate contradictory retrieved evidence with disagreement among
    scorers.
20. Do not claim a contradictory-context experiment was completed.
21. Do not claim universal submitted per-query coverage. Recovered rows must
    be labeled as recovered.
22. Do not assert immutable preregistration timing or exact historical
    package/model revisions.
23. Do not claim a full manuscript rewrite has already been completed.
24. Do not call the current/initial AC note the final meta-review.
25. Do not include confidential review transcripts, external-rater identity,
    private contacts, credentials, personal absolute paths, or deanonymizing
    links in the public branch or paste text.
