# Result Ingestion Runbook

## Quarantine first

Treat a downloaded result ZIP as untrusted and optional. Do not place it in
the submitted artifact or cite it until every gate below passes. Record its
SHA-256 before extraction and extract into a temporary directory.

## Acceptance gates

1. ZIP contains only the `BUILD_RESULT_ZIP.py` allow-list.
2. Run config uses the frozen candidate, source SHA, prompt/parser versions,
   provider, exact model/revision, temperature, and fallback limit.
3. Candidate manifest hash matches the committed candidate index.
4. Final JSONL has exactly one record per candidate `row_id`, no unknown IDs,
   and no duplicates.
5. Every `input_digest` matches the source join.
6. Every returned model, `X-Routed-Via`, and `X-Fallback-Attempts` satisfies
   the frozen routing policy.
7. Raw and parsed outputs are both present; parse/refusal/error rates are
   reported without manual repair.
8. Runtime metadata confirms the declared quantization, dtype, GPU topology,
   and strategy.
9. `POST_RUN_ANALYSIS.py` reports `scientifically_valid=true`.
10. A privacy/secret scan finds no credentials, authorization headers,
    identity data, private review text, or personal paths.

Pass the frozen route allow-list through one
`--allowed-routed-via VALUE` argument per allowed value and retain the default
zero fallback limit unless the pre-registration explicitly states otherwise.

Any failed routing, duplication, source, or privacy gate blocks scientific
use. A partially complete run may be diagnosed but must not supply a headline
effect.

## Analysis and wording

Use the preregistered primary paired contrast first. Report sample size,
complete-pair count, estimate, 95% paired bootstrap CI, provider/model pin,
prompt version, parse/error rates, and output origin. Secondary contrasts and
correlations must be labeled secondary.

Do not:

- replace locked submitted average-precision values;
- pool the `n=99` and `n=100` human slices;
- call the modern judge ground truth or universally correct;
- call fixed-output rescoring fresh retrieval/generation;
- claim broader generator/dataset coverage; or
- make the rebuttal depend on the optional result.

## Git decision

Prompt 6 should decide whether any aggregate, sanitized result belongs on the
branch. Raw model outputs may contain unsafe text and should not be committed
automatically. Never commit caches, weights, checkpoints, credentials, or the
unredacted runtime secret environment.
