#!/usr/bin/env bash
# Lightweight verification entry point for the anonymized artifact.

set -euo pipefail

cd "$(dirname "$0")"

python3 scripts/verify_human_eval.py
python3 scripts/analyze_human_disagreement_labels.py
