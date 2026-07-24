# Result Ingestion Runbook

## Quarantine first

Treat any result ZIP as optional and untrusted. Hash it before extraction and
extract to a temporary directory. Do not cite or commit raw outputs
automatically.

## Required files and provenance

The deterministic ZIP must contain exactly the allow-listed run config,
candidate manifest, attempt log, terminal final JSONL, checkpoint, runtime
metadata, and post-run analysis. It must contain no scratch/cache directories,
secrets, credentials, symlinks, model files, or unknown top-level files.

Verify:

1. source and manifest hashes match config and committed candidate index;
2. prompt v2/parser v2, canonical prompt digests, transport, label thresholds,
   generation settings, retry budget, and strict gates match the frozen config;
3. provider, exact model/revision, returned model, route, and fallback
   metadata match for every applicable attempt;
4. actual dtype, quantization, device/GPU topology, model-source mode, library
   versions, context policy, token counts, and finish reasons are recorded;
5. attempt keys are unique, contiguous, within budget, and append-only;
6. no attempt follows terminal state, successful rows never rerun, and only
   eligible parse/provider failures retry;
7. each final row equals the last terminal attempt for that row;
8. final JSONL has exactly one terminal row per manifest ID, no missing,
   extra, duplicate, or unknown row;
9. raw output remains exact and score/derived-label/reason satisfy schema;
10. partial JSONL, corrupt checkpoint, prompt changes, and conflicts are
    absent.

## Strict scientific gates

Run `POST_RUN_ANALYSIS.py` with `--manifest`, `--source`, `--results`,
`--attempts`, `--config`, `--template`, and `--output`. The saved summary must
report:

- all manifest rows terminal and `ok`;
- zero parse/provider/routing/integrity/configuration failures under default
  thresholds;
- zero condition error-rate difference;
- consistent source, manifest, prompt, model, provider, routing, and attempt
  history;
- candidate/successful/excluded pairs and causes for every contrast; and
- the primary complete-pair minimum passed.

Any strict gate failure sets `scientifically_valid=false` and
`NOT_REBUTTAL_SAFE_STRICT_GATE_FAILURE`. Diagnostic complete-case estimates
must not become rebuttal claims.

## Privacy and interpretation

Scan for credentials, authorization headers, identity data, confidential
review text, personal paths, prompt-injected secrets, and unsafe raw content.
Raw output may be unsuitable for a public repository even when numerical
gates pass.

Any accepted aggregate must state candidate size, complete pairs, estimate,
paired CI, prompt/parser versions, provider/model pin, retry/error counts,
output origin, and fixed-output boundary. Never replace locked submitted
metrics, pool the `n=99`/`n=100` slices, call the judge ground truth, call
rescoring fresh retrieval/generation, or claim broad generalization.
