# Decision Log

## D01 — Resolve the nested worktree conservatively

The prompt diagram places Git at `raghal_ingest_workspace_20260724/`, but that
directory has no `.git`. Its nested `raghal/` directory is the valid Git root.
All outputs were therefore placed under
`raghal/controlledrag_neurips_rebuttal_workspace_20260724/`.

## D02 — Block all pushing

Authenticated metadata confirms the target repository is public. The required
status is `PUSH_BLOCKED_REPOSITORY_PUBLIC`. Prompt 01 is committed locally
only.

## D03 — Do not store exact review text

Because the repository is public, only sanitized concern paraphrases are
allowed. Moreover, no exact five-review or AC/meta-review export was located.
Reviewer IDs, scores, confidence values, and per-review attribution remain
`SOURCE_MISSING`; no mapping was invented.

## D04 — Prefer the submitted artifact for submitted-value provenance

The standalone submitted tree is clean at
`59e94a5418a296acda1892e9165fd43096292f58`. Cleanup material is a candidate
evidence source, not an automatic replacement.

## D05 — Preserve the AUPRC conflict

Cleanup snapshots use a manual AUPRC calculation, while the submitted
implementation uses `sklearn.metrics.average_precision_score`. The submitted
results are `0.765 / 0.929 / 0.859` after paper rounding; historical cleanup
values must not be mixed in. Prompt 01 records the conflict but does not verify
either implementation numerically.

## D06 — Keep human-evaluation arms separate

The `n=99` typical-row calibration and `n=100` targeted disagreement slice use
different sampling and label schemas. They remain separate ledger entries and
must never be pooled.

## D07 — Bound re-encoding and generalization language

BGE/E5 matched-context evidence is fixed-context re-encoding, not a fresh
end-to-end retrieval/generation experiment. Qwen2.5 and long-form findings are
bounded probes. Context-conditioned NLI is evidence that calling convention
matters, not a universally correct scorer.

## D08 — Do not mark numerical claims verified

Prompt 01 performs extraction and prioritization only. Every numerical claim
is `TO_VERIFY` or, where only an aggregate is available, `SUMMARY_ONLY`.

## D09 — Lock submitted sklearn average precision

The submitted `n=100` script and independent recomputation agree on AUPRC
`0.764813 / 0.928793 / 0.859367`. Historical
`0.761753 / 0.928433 / 0.886240` values are superseded and quarantined.

## D10 — Quarantine the matched `p=0.011`

The 9-versus-24 discordance reproduces the reported rates but not `p=0.011`.
The exact two-sided value is `0.013531`; the uncorrected asymptotic value is
`0.009023`. The rates remain safe, while the claimed p-value is excluded.

## D11 — Pass P0 through explicit exclusions

P0 passes only because all mismatched, pending, and not-safe items are barred
from proposed rebuttal text. No unresolved number is silently promoted.

## D12 — Preserve output origins

Fixed-context re-encoding, fixed-generation rescoring, imported pilot
summaries, original generated rows, aggregated statistics, and manually
curated provenance decisions are labeled separately in the ledger.

## D13 — Keep n=99 binary metrics secondary

The `n=99` primary endpoint is ordinal. Prompt 03 does not invent an all-row
binary collapse. A secondary sensitivity excludes all 16
partially-supported rows, leaving 83 determinate rows and only four negatives;
it is not headline evidence.

## D14 — Correct legacy NLI naming

Code inspection confirms that the default legacy DeBERTa and second-NLI
zero-shot calls do not consume retrieved context. Their fixed values remain
historically valid, but rebuttal wording must call them answer-only
zero-shot label proxies.

## D15 — Treat scorer ordering as slice-dependent

RAGAS-style exceeds second NLI on the typical `n=99` slice, while their direct
ordering is unresolved on the disagreement-targeted `n=100` slice. Prompt 03
does not declare a universal best scorer.

## D16 — Bound context, threshold, and cost findings

Context-conditioned results are fixed-context re-encoding sensitivities.
Threshold transfer is mixed across the fixed five-dataset grid. Pareto and
cost-weight findings are point-estimate, two-dataset sensitivities. None is
promoted to universal generalization.

## D17 — Apply the Prompt 04 public-safe push override

Prompt 04 explicitly authorizes pushing the dedicated branch even though the
repository remains public. The earlier visibility-only block is superseded,
while scoped staging, sanitization, secret scanning, and remote verification
remain mandatory.

## D18 — Frame seven axes as a practical disclosure minimum

The seven axes are practical non-redundant disclosure categories for this
audit, not a mathematically unique or formally exhaustive taxonomy. All seven
are disclosed; only claim-critical reasonable alternatives require stress
testing.

## D19 — Interpret Figure 2 as measurement sensitivity

Figure 2 holds fixed answers and contexts and varies the NLI input
convention. The sign reversal demonstrates that calling convention matters.
It is not fresh retrieval/generation and does not establish a universally
correct context-conditioned scorer.

## D20 — Preserve a paired, nested candidate design

Candidate selection ranks query groups rather than independent condition
rows. This maximizes complete paired comparisons, keeps 300/400/500/600
candidates nested, and reaches non-multiples of three with at most two
deterministic extras.

## D21 — Keep manifests text-free

Committed manifests contain only join indices, stable IDs, grouping metadata,
and hashes. Raw question/context/answer text remains in the locked fixed
source and is joined only in an authorized execution environment.

## D22 — Fail closed on model routing

Reported runs must hard-pin provider/model and reject unexpected returned
models, routes, missing routing headers, or fallback attempts. Provider fusion
and `model="auto"` are prohibited.

## D23 — Stop Prompt 05 at build-only validation

Only synthetic/mock tests are permitted. No model load, network call, real
row scoring, Kaggle/Colab launch, or result interpretation is part of Prompt
05, and the rebuttal remains complete without the optional run.
