# Prompt B completion receipt

Date: 25 July 2026.

## Audit verdict

The accepted run's raw records, strict parser, model identity, analysis populations, and aggregate statistics independently pass. The strong inclusion gate passes. Prompt B is not globally complete because the separately named repair ZIP was not located and the anonymous mirror has not refreshed to the published source `main`.

Final status:

`PROMPT_B_BLOCKED`

Exact blockers:

- `REPAIR_ZIP_NOT_LOCATED_CROSS_ZIP_IDENTITY_UNVERIFIED`
- `BLOCKED_BY_ANONYMOUS_MIRROR_REFRESH`

## Package and checksum receipt

Project-relative private paths:

| Artifact | Path | SHA-256 | Internal checks |
| --- | --- | --- | --- |
| frozen input | `CONTROLLEDRAG_TARGETED_JUDGE_INPUT.zip` | `1ded9189578cf2af353d58bae073a14ff4e6e064ef485f23dd85c686c721a456` | 54/54 pass |
| accepted output | `CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT_POSTPROCESSED.zip` | `3e00950596cf982c93030b32e626725a69ac0f4965aef2bca993d0d08e874311` | 34/34 pass |
| separately named repair archive | `CONTROLLEDRAG_TARGETED_JUDGE_LEFT_PADDING_FAILED.zip` | not located | unavailable |

The accepted output contains both raw shards, the merged raw file, validation records, the model receipt, and the repair lock. Shard-to-merge record equivalence passes for all 1,510 keys. Cross-ZIP identity cannot be checked without the missing archive; no substitute was created.

## Model and repair receipt

- model: `Qwen/Qwen2.5-7B-Instruct`
- immutable revision: `a09a35458c702b33eeacc393d103063234e8bc28`
- identity mismatches: 0/1,510
- decoder-only left padding is the recorded execution repair
- raw output repair or imputation: none
- new inference or API calls during Prompt B: none

## Validity and populations

- requested: 1,510
- received: 1,510
- valid: 1,507
- invalid: 3
- invalid category: threshold inconsistency, preserved
- missing, duplicate, unexpected, or identity-error keys: 0
- validity rate: 99.801%
- differential missingness: 0.781 percentage points
- inclusion gate: `STRONG_INCLUSION_GATE_PASS`
- preregistered candidate pairs: 194
- primary common-complete pairs: 193
- typical human-labelled slice: 83
- disagreement-targeted diagnostic slice: 72

## Independent results

All point estimates below are direct observed estimates. Intervals use a paired percentile bootstrap with seed 20260724 and 10,000 requested replicates.

| Result | Direct estimate | 95% CI | Finite replicates |
| --- | ---: | ---: | ---: |
| answer-only baseline minus HCPC-v1 | 3.31606 points | [0.46632, 6.26943] | 10,000 |
| context-conditioned baseline minus HCPC-v1 | 13.93782 points | [9.53368, 18.23834] | 10,000 |
| difference in contrasts | 10.62176 points | [5.54404, 15.49223] | 10,000 |
| typical AP, context minus answer | 0.018911 | [0.004408, 0.042169] | 9,822 |
| typical Spearman, context minus answer | 0.132954 | [0.060721, 0.215056] | 9,822 |
| diagnostic AP, context minus answer | 0.065694 | [0.016305, 0.119333] | 10,000 |
| diagnostic Spearman, context minus answer | 0.246286 | [0.023418, 0.506260] | 9,991 |

On the typical slice, AP changes from 0.962788 to 0.981699 and Spearman from 0.117791 to 0.250745. On the separate diagnostic slice, AP changes from 0.798559 to 0.864252 and Spearman from 0.052908 to 0.299195.

## Claim and package decision

Supported with scope:

- material scorer-input sensitivity under one pinned modern judge;
- same-direction system contrasts with a 10.62-point difference in magnitude;
- better context-conditioned human alignment on the audited 83- and 72-row slices;
- a strong inclusion-gate pass with preserved invalid outputs.

Not supported:

- universal evaluator correctness or superiority;
- a sign reversal;
- broad validation across every RAG setting;
- arbitrary long-form or agentic generalisation.

Package recommendation: `FALLBACK_NO_NEW_RESULTS` until both blockers are cleared. The preferred package is scientifically bounded and ready for professor review, but it should not be submitted while cross-ZIP provenance and the live mirror remain unresolved.

## Privacy, formatting, and release

- private rows in Git: 0
- individual human labels in Git: 0
- raw judge outputs in Git: 0
- ZIPs in Git: 0
- absolute local paths, credentials, and tokens in the Prompt B release: 0
- preferred character counts: 3,825 / 2,086 / 1,943 / 2,805 / 1,967 / 2,321; all pass the 10,000-character limit
- fallback character validation: pass
- Markdown/plain-text synchronization: pass
- source release gates: 13/13 pass
- source mathematical tests: 19/19 pass

## Git receipt

Source artifact repository:

- start: `4aca9ae3442454d40effae4354b87e18a3de42c3`
- cleanup content: `62027ae80e32126110ffe3a70a03779154d9e412`
- `main` integration: `d26b29ee810c289e44233881f78364656f3d0612`
- receipt: `37b3520f035e9b22ddbb606b4c5027abd88ee79a`
- remote `main`: verified by local tracking ref and `git ls-remote`

Rebuttal repository:

- start: `fa3e8dd405e0b068fd1502b9075f1d9d7fed60db`
- results: `b444062f0fbc4d7bc306c26a6f7d58bd8f8c8720`
- rebuttal and author pack: `e98a3132fb0eea2f52fb1db7caf8aa32d24b82e6`
- `main` integration: `473deffb72c5f65ddb268eb84567bc9780141cb5`
- receipt commit: `self`
- remote integration: local HEAD, tracking ref, `git ls-remote`, and GitHub API matched

Neither repository was force-pushed. Both working branches and pre-edit backup refs are preserved.

## Human actions remaining

1. Locate and provide the separately named repair ZIP, then compare its raw outputs with the accepted postprocessed package.
2. Refresh the anonymous mirror from the published source `main`, visually inspect it, and confirm its README and aggregate tables match the release.
3. Obtain professor approval of the preferred-versus-fallback decision.
4. Review rendering in every OpenReview field.
5. Submit manually. Codex did not submit anything.
