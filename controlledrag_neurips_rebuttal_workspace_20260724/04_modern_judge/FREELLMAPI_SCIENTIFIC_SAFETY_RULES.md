# FreeLLMAPI Scientific Safety Rules

1. Hard-pin one provider and one exact model. Never use `auto`.
2. Disable fusion, provider blending, and silent fallback.
3. Require and retain the returned model, `X-Routed-Via`, and
   `X-Fallback-Attempts` for every row.
4. Reject, do not reinterpret, an unexpected model, route, missing routing
   header, malformed fallback count, or fallback count above the frozen limit.
5. Choose the sample size before seeing outputs; do not switch candidates
   because of the result.
6. Freeze prompt, parser, temperature, token limit, label anchors, and retry
   rules before the first call.
7. Retry transport failures only; never retry selectively by condition,
   label, score, or apparent correctness.
8. Log raw output and parsed output separately. Parser failures remain visible
   and are never hand-corrected silently.
9. Write exactly one final record per `row_id`; retain attempts separately.
10. Never log or package credentials, authorization headers, private contact
    information, external-rater identity, or confidential review text.
11. Do not pool the `n=99` and `n=100` human slices in later alignment.
12. Describe any accepted result as optional fixed-output rescoring on a
    bounded SQuAD/Mistral panel—not a universal judge validation or fresh
    end-to-end experiment.
13. The rebuttal must remain complete if the run fails, reroutes, or is never
    executed.
