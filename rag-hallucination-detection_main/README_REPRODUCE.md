# Reproducing ControlledRAG Results

This document explains how to run the anonymized verification path for the
ControlledRAG reproducibility artifact. The default commands read frozen CSVs
already included in the repository. They do not rerun generation, retrieval,
or model scoring.

## Setup

Use Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The default `requirements.txt` contains only analysis dependencies:
`numpy`, `pandas`, `scipy`, and `scikit-learn`.

## Lightweight Verification

Run the default verification:

```bash
bash run_all_analysis.sh
```

This runs:

```bash
python3 scripts/verify_human_eval.py
python3 scripts/analyze_human_disagreement_labels.py
```

It should complete quickly on a laptop CPU.

## Expected Human-Evaluation Values

Typical-row calibration:

```bash
python3 scripts/verify_human_eval.py
```

Expected values for `n=99`:

| Quantity | Value |
| --- | --- |
| raw agreement | 0.919 |
| Cohen's kappa | 0.774 |
| adjudicated distribution | 79 supported / 16 partially supported / 4 unsupported |
| Spearman correlations | 0.103 / 0.394 / 0.549 |

Targeted disagreement slice:

```bash
python3 scripts/analyze_human_disagreement_labels.py
```

Expected values for `n=100`:

| Quantity | Value |
| --- | --- |
| raw agreement | 0.88 |
| Cohen's kappa | 0.721 |
| adjudicated distribution | 74 faithful / 26 hallucinated / 0 unclear |
| Spearman correlations | -0.156 / 0.446 / 0.384 |
| AUROC | 0.398 / 0.794 / 0.718 |
| AUPRC | 0.765 / 0.929 / 0.859 |

There is no pending-label state for the `n=100` slice.

## Frozen File Locations

- `human_eval_final/n99_calibration/`: final `n=99` annotation and summary files
- `human_eval_final/n100_disagreement/`: final `n=100` targeted disagreement files
- `results/revision/`: frozen result tables for reported analyses
- `results/multi_retriever/`: frozen stronger-retriever summary files
- `source_tables/`: compact table inputs used by the paper
- `data/revision/fix_06/per_query_compact.csv`: compact numeric source for the cost-aware verification script
- `data/revision/`: additional frozen source CSVs used by optional regeneration scripts

See `SOURCE_TRACE.md` and `CLAIMS_AUDIT.md` for claim-to-file mapping.

## Lightweight vs. Expensive Scripts

Lightweight scripts:

- `scripts/verify_human_eval.py`
- `scripts/analyze_human_disagreement_labels.py`
- `scripts/compute_standardized_scorer_fragility.py`
- `scripts/compute_matched_ccs_distribution.py`
- `scripts/compute_cost_headtohead_cis.py`
- `scripts/compute_nli_human_correlation.py`
- `run_all_analysis.sh`

Expensive scripts:

- `experiments/fix_*.py`
- `experiments/run_*.py`

The expensive scripts can regenerate selected frozen CSVs, but they are
not needed for review-time verification. They require local model runtimes,
embedding models, and substantially more wall-clock time.

## Hardware Assumptions

The lightweight path runs on a normal laptop CPU. No paid APIs are
required.

Full regeneration of model outputs is outside the default verification
path. It assumes a local model runtime and can take several hours.

## Troubleshooting

- If imports fail, confirm the virtual environment is active and rerun
  `pip install -r requirements.txt`.
- If a verification script cannot find an input CSV, run it from the repository root.
- If `run_all_analysis.sh` stops early, run the two human-evaluation commands above first.
- If you need the full experiment dependency set, install
  `requirements-full.txt` in a separate environment.
