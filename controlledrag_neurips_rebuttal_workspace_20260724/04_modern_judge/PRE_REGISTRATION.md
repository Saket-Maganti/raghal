# Optional Modern-Judge Pre-Registration

## Status and timing

This is a prospective plan for an optional post-submission analysis. It is
not evidence that the original study was preregistered, and it creates no
result. Prompt 05 prepared and synthetically tested code only.

## Research question

On the fixed 600-row SQuAD/Mistral panel, does a hard-pinned modern
question+context+answer judge reproduce, attenuate, or reverse the
baseline-minus-aggressive-refinement score contrast? This is rescoring of
fixed outputs, not fresh retrieval or generation.

## Candidate sample sizes

Four deterministic, condition-balanced candidates are frozen: 300, 400, 500,
and 600 rows. The primary candidate is 600 if resources permit. Smaller
candidates are operational fallbacks, not sequential looks selected by
outcome. The final size must be chosen before any real output is inspected and
recorded in the run config.

## Sampling

`SAMPLE_SELECTION.py` verifies the source SHA-256, builds a stable row ID from
the fixed input fields, ranks complete query groups using SHA-256 with salt
`controlledrag-modern-judge-v1`, and takes groups in that order. At most two
deterministic condition-ordered extra rows are added to reach 400 or 500
exactly. The candidates are nested, condition counts differ by at most one,
and complete paired comparisons are maximized. Manifests omit raw text and
prior score values.

## Judge and prompt

The provider, model ID/revision, quantization, prompt version, parser version,
and decoding settings must be hard-pinned before execution. `model="auto"`,
provider fusion, silent fallback, and unexpected rerouting are prohibited.
The prompt asks for one support label, a score in `[0,1]`, and a short reason
using the question, retrieved context, and fixed answer.

## Primary endpoint

Mean paired `baseline - hcpc_v1` judge-score contrast over query pairs that
are complete in both conditions, with a 10,000-resample paired percentile
bootstrap 95% CI. Positive means baseline receives the higher support score.

## Secondary endpoints

- `hcpc_v2 - hcpc_v1` and `baseline - hcpc_v2` paired contrasts;
- per-condition score means and label distributions;
- parse, refusal, error, and routing-rejection rates;
- Spearman correlations with the three existing fixed-output scorers;
- scorer-to-human alignment only when joined separately to the `n=99` or
  `n=100` adjudicated slice, never by pooling those slices.

Secondary endpoints are descriptive and must be labeled post-primary.

## Exclusions

Exclude only rows with a recorded provider error, rejected routing, or output
that fails the frozen parser. Do not retry selectively by condition or based
on score. Report every exclusion and retry count. Duplicate `row_id` values
are a hard failure.

## Routing and reproducibility gates

A run is scientifically invalid if the returned provider/model differs from
the requested pin, if `X-Routed-Via` is unexpected, if
`X-Fallback-Attempts` is nonzero without explicit prior authorization, or if
the provider omits required routing metadata. Raw and parsed outputs,
request/response metadata, hashes, checkpoints, and run config must be
retained.

## Interpretation limits

The analysis can add one bounded scorer sensitivity to a fixed SQuAD/Mistral
panel. It cannot establish a universally best judge, broad RAG
generalization, or fresh end-to-end replication. The rebuttal does not depend
on this optional result.
