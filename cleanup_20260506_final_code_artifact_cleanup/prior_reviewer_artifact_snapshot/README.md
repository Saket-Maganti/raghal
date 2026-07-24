# ControlledRAG Reproducibility Artifact

This repository contains the anonymized code and frozen artifacts needed to
verify the ControlledRAG RAG faithfulness audit. It is intended for
double-blind review and includes only reproducibility instructions, scripts,
frozen result tables, and human-evaluation artifacts.

## Repository contents

- `scripts/`: verification and analysis scripts
- `src/`: reusable project code
- `experiments/`: experiment entry points or configs
- `data/`: frozen/small data artifacts required by scripts
- `results/`: frozen result tables used by the paper
- `source_tables/`: source CSVs for reported claims
- `human_eval_final/`: final human-evaluation files
- `tests/`: smoke tests
- `run_all_analysis.sh`: lightweight verification entry point
- `README_REPRODUCE.md`: detailed reproduction instructions

## Quick start

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    bash run_all_analysis.sh

## Verify human evaluation

    python3 scripts/verify_human_eval.py
    python3 scripts/analyze_human_disagreement_labels.py

Expected values:

Typical-row calibration (`n=99`):
- raw agreement: 0.919
- Cohen's kappa: 0.774
- adjudicated distribution: 79/16/4
- Spearman correlations: 0.103/0.394/0.549

Targeted disagreement slice (`n=100`):
- raw agreement: 0.88
- Cohen's kappa: 0.721
- adjudicated distribution: 74/26/0
- Spearman correlations: -0.156/0.446/0.384
- AUROC: 0.398/0.794/0.718

## Reproducing paper tables

See `README_REPRODUCE.md`.

## Notes

- Generation outputs are frozen and are not rerun by default.
- Heavy model jobs are separated from lightweight verification.
- No paid APIs are required for the verification path.
- This repository is anonymized for double-blind review.
