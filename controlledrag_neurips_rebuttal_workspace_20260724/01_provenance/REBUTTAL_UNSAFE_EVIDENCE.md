# Rebuttal-Unsafe Evidence

## Numerical mismatches

### Matched binary tail tests (`CR-012`, `CR-013`)

The row-level table has 9 LOW-only and 24 HIGH-only discordant pairs. The
reported rates reproduce: 16.5% versus 9.0% hallucination and 17.0% versus
27.0% answer-span presence. The claimed `p=0.011` does not.

- exact two-sided binomial/McNemar: `p=0.013531`;
- asymptotic chi-square without continuity correction: `p=0.009023`;
- neither standard convention rounds to `0.011`.

The rates are safe. The `0.011` p-value is not safe.

## Artifact/provenance mismatches

- `CR-059` and `CR-062`: the universal claim that the submitted artifact
  contains per-query CSVs for every audited cell is false as written.
- `CR-060`: a historical internal `audit_log.md` says `2026-04-26`, but the
  standalone submitted repository exposes only a later clean-artifact commit.
  No immutable pre-result Git timestamp was located.
- `CR-061`: compensation and IRB statements were not author-confirmed for
  this workflow.

## Restricted interpretation

- The matched BGE/E5 panel is re-encoding of fixed contexts.
- The multi-retriever panel is a separate `n=30`-per-cell pilot.
- The context-conditioned NLI panel is rescoring on fixed generations; only
  194 paired rows are complete for each context-conditioned backbone.
- Qwen is one fixed-context, one-generator probe.
- Long-form is an exploratory 40-question probe.
- Cost and latency values are harness- and hardware-specific.
- Threshold transfer is descriptive and has no uncertainty intervals.
- Noise slopes are point estimates without significance tests.

These restrictions do not invalidate the verified arithmetic. They define
the maximum rebuttal-safe claim scope.
