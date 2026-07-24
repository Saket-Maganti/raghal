# Analysis Limitations

## Human evaluation

- The `n=99` panel is small and has only four adjudicated unsupported rows.
  Its determinate-only AUROC/AP sensitivity is unstable and base-rate-heavy.
- The `n=100` panel was selected for scorer disagreement. Its 74% faithful
  share is not a population prevalence estimate.
- The panels use different label schemas and sampling designs and cannot be
  pooled.
- Rater qualifications, compensation, IRB status, LLM assistance, and
  adjudicator identity are unconfirmed.

## Metric implementation

- The two legacy NLI columns are answer-only zero-shot label proxies despite
  context-oriented documentation.
- The RAGAS-style scorer is a custom LLM prompt, not the official `ragas`
  package.
- Submitted requirements use lower bounds. Exact Transformers, PyTorch,
  LangChain, tokenizer, model-weight, and local judge revisions are not
  locked.
- Fixed scores can be audited numerically, but bitwise model-score
  regeneration is not claimed.

## Existing-output analyses

- Context-conditioned NLI covers a fixed 600-row subset, with 194 complete
  baseline/HCPC-v1 pairs for each context scorer. It is re-encoding of
  existing context and answers, not fresh retrieval or generation.
- A context-conditioned pair formulation is more semantically direct than
  the legacy proxy, but it is not established as universally correct.
- Threshold transfer is a descriptive five-dataset grid. It does not show
  out-of-domain universality.
- Pareto status uses point estimates and two datasets; it is not a
  statistical dominance test.
- Cost-weight utility uses illustrative query volumes and time penalties.
- The matched binary `p=0.011` remains excluded; exact two-sided
  `p=0.013531` is the only safe replacement when its convention is stated.
- No new modern-judge result is required or used.

## Provenance and tooling

- Some complete per-query inputs are recovered rather than shipped in the
  submitted artifact. Every such origin is labeled and hashed.
- Exact review/meta-review text remains unavailable, so reviewer-specific
  response mapping is still blocked.
- The artifact-tool spreadsheet inspection backend could not load because
  macOS rejected its bundled native module signature. Reproducible Python,
  CSV-schema, and hash checks were used. No workbook was created.
- The target repository is public; pushing rebuttal material remains blocked.
