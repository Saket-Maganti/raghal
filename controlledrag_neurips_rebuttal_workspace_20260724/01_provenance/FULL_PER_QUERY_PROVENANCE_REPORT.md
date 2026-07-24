# Full Per-Query Provenance Report

## Outcome

Prompt 02 independently recomputed the rebuttal-relevant numerical claims
from fixed local files without model inference or network access. The
62-claim ledger now contains source files, scripts, configurations, SHA-256
hashes, recomputed values, tolerances, output origins, verification statuses,
and rebuttal-safety limits.

Status totals:

| Status | Claims |
| --- | ---: |
| `VERIFIED_EXACT` | 4 |
| `VERIFIED_WITH_ROUNDING` | 50 |
| `VERIFIED_SUMMARY_ONLY` | 2 |
| `MISMATCH` | 4 |
| `PROVENANCE_MATCH_PENDING` | 1 |
| `NOT_REBUTTAL_SAFE` | 1 |

## Headline verification

| Claim group | Independent result | Status and scope |
| --- | --- | --- |
| Matched similarity/CCS | Similarity `0.423588 / 0.421478`; CCS `0.670060 / 0.137426` | Verified with rounding |
| Matched faithfulness | HIGH−LOW `-0.002392`; Wilcoxon `W=8638.5`, one-sided `p=0.628268`; `dz=-0.017086`; bootstrap CI `[-0.021651,+0.016819]` | Verified; matched SQuAD cell only |
| Matched binary tail | Hallucination `16.5% / 9.0%`; discordance 9/24 | Rates verified; claimed `p=0.011` mismatches exact `p=0.013531` |
| Span diagnostic | Span `17.0% / 27.0%`; R2 span/CCS/similarity `0.018964/0.003003/0.001941`; joint `0.024702`; AUROC CCS/similarity/span `0.639249/0.585819/0.531238`; joint `0.643126` | Models refit from 400 fixed rows; post-hoc |
| Scaled audit | Faithfulness `0.660947/0.650271/0.661196`; hallucination `0.1460/0.1472/0.1428`; similarity `0.532193/0.568948/0.532152`; gate rate `0.7048` | Verified from 7,500 rows |
| Per-seed scaled contrasts | Baseline−v1 significant only seed 44 (`p=0.008163`); gated−v1 significant seeds 41/44/45 | Verified; small effects |
| Scorer fragility | Raw `0.010495/0.031727/0.139262`; z `0.070904/0.230782/0.336568`; rank `0.021704/0.062334/0.084650` | Verified from fixed generations; 2,499 paired keys |
| Cross-scorer Pearson | `0.258666/0.181871/0.674177` | Verified; input-format confounding remains |
| Context-conditioned sign change | DeBERTa legacy `+0.016774`, context `-0.278689`; roberta legacy `+0.044187`, context `-0.081418`; RAGAS `+0.129850` | Verified as rescoring; context columns have 194 pairs |
| Human `n=99` | Agreement `0.919192`; kappa `0.773779`; labels `79/16/4`; Spearman `0.103023/0.393969/0.548699` | Verified; typical slice |
| Human `n=100` | Agreement `0.880000`; kappa `0.720930`; labels `74/26/0`; Spearman `-0.156045/0.446432/0.384277` | Verified; targeted slice |
| Submitted `n=100` AUROC/AUPRC | AUROC `0.397609/0.793659/0.717516`; AUPRC `0.764813/0.928793/0.859367` | Verified with submitted sklearn AP |
| Threshold transfer | Selected taus PubMedQA `.4`, NaturalQuestions `.5`, SQuAD `.3`, TriviaQA `.4`, HotpotQA `.3`; submitted matrix reproduced | Verified descriptive matrix; no CIs |
| Cost/head-to-head | SQuAD faithfulness `0.698205/0.708378/0.710022`; HotpotQA `0.642749/0.633429/0.630825` | Verified; harness-specific |
| Latency/indexing | SQuAD `1440.488/1719.940/1713.704` ms; HotpotQA `1940.647/2288.938/2413.582` ms; RAPTOR indexing `21.892x/16.821x` dense | Verified; hardware-specific |
| Fixed-context re-encoding | CCS gaps MiniLM `0.532634`, BGE `0.248781`, E5 `0.127309` | Verified; re-encoded, not fresh retrieval |
| Multi-retriever pilot | SQuAD MiniLM `+0.075317`, BGE `+0.032017`, E5 `-0.011280`, GTE `-0.001463`; PubMedQA all positive | Verified from recovered 720-row pilot |
| Qwen probe | Raw contrasts `0.014584/0.045547/0.134000`; Pearson `0.379549/0.280120/0.721134` | Verified; 100 rows/condition |
| Long-form probe | 20 MS-MARCO + 20 QASPER questions; span means reproduced; baseline−v1 `-0.033170/+0.001930` | Verified; exploratory |
| Noise slopes | Random faith/sim `-0.068592/-0.481012`; coherent `-0.043224/-0.112629` | Verified point estimates |

Condition order is baseline/aggressive/gated where three values are shown,
unless the row names another order.

## Safe fixed-data inputs

| Evidence | Rows | SHA-256 |
| --- | ---: | --- |
| Fix 01 matched per-query | 400 | `d8666081a1833c21263e0a5c87074a2f4a4db8d3d095c5ec18a367f5c99c2a99` |
| Fix 02 scaled per-query | 7,500 | `bd6a0b8aac42c695c502c14c64748fd9ed4ae37d7e67d87d80ffb62f474d469e` |
| Fix 03 scorer per-query | 7,500 | `f046d7646c68fb50084781ad8cee962991b45b9f292714a50d2f4570d5c07859` |
| Context-conditioned `n=600` | 600 | `78348a4a786434fbf5aa42e1179f7c81aae7695eaee4e876d145aa3cb1a575f4` |
| Fix 04 threshold per-query | 7,500 | `d72b14793e6389bbe2b291a35aa351c7cfbc36f57f1d4feea8d15c83d1f431df` |
| Fix 05 noise per-query | 1,591 | `b74b3bdfbf4a2d6855eba395f31805e0154a51315353fddac37d6d284ef6dbba` |
| Fix 06 cost per-query | 1,200 | `feafac8c1eedbd69768762af5a46b43902f2a5bc4a5fb7da5f746f61ca6c3f89` |
| Fix 12 span/control rows | 400 | full hash in claim ledger |
| Fix 13 re-encoded rows | 1,200 | `9bedc34a9bb20735ecf50fb64c7c4951ae219fd2366952701ecb9a83e1c0423f` |
| Multi-retriever pilot | 720 | `782abf51ed1f2c4d5be45c28228a8bf073b8b21465defd8347dc11ba97fcc880` |
| Qwen probe | 300 | `7235ec54f6ee57a4a22e611b2e8f6a6ddc9cf3f0ed8540ad327c3c190e234c84` |
| Long-form probe | 120 | `eafc34ae6ca91e5babe9075c4050f6f8dd140d7b6e5c52bea16760f7fbcf9b64` |
| Human `n=99` adjudicated | 99 | `872b89ca3896769e82c8addc819b2d11c869458927ecb4f816dbda4b0317b4f4` |
| Human `n=100` annotated/scored | 100 | `83ac395bdce120c3b8def310e410191fb2969942d6796dd57dc48dd3dc5643b8` |

Recovered inputs are safe for analysis only when their provenance limitation
is stated. They are not silently relabeled as submitted files.

## Output-origin controls

- `generated`: original retrieval/generation rows.
- `rescored`: fixed answers evaluated by additional scorers.
- `re-encoded`: fixed contexts embedded again without new retrieval or
  generation.
- `imported`: copied from another existing result panel.
- `aggregated`: computed summary/statistic from fixed rows.
- `manually curated`: conceptual or provenance decision.

Composite labels in the claim ledger show the full chain, such as
`generated; rescored; aggregated`.

## Reproducibility

`verify_prompt02_fixed_data.py` performs the fixed-data recomputation and
writes `PROMPT_02_RECOMPUTED_RESULTS.json`. It invokes no model, API, dataset
download, or network service.

The spreadsheet artifact validator could not load its native rendering
dependency because macOS rejected the bundled native module's code signature.
CSV shape, header uniqueness, row count, allowed-status vocabulary, and
required-field completeness were therefore validated with Python and shell
checks instead. This tooling issue does not affect numerical recomputation.
