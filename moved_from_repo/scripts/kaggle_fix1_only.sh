#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-mistral}"
OLLAMA_LOG="${OLLAMA_LOG:-/kaggle/working/ollama.log}"
export OLLAMA_LOG

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] [fix1-only] $*"; }
section() { echo; echo "[$(ts)] ===== $* ====="; }

row_count() {
  local path="$1"
  if [ -s "$path" ]; then
    python - "$path" <<'PYROW'
import pandas as pd, sys
try:
    print(len(pd.read_csv(sys.argv[1])))
except Exception:
    print("?")
PYROW
  else
    echo 0
  fi
}

run_with_heartbeat() {
  local label="$1"
  local csv_path="$2"
  local expected_rows="$3"
  shift 3
  local start
  start=$(date +%s)
  section "$label"
  "$@" &
  local pid=$!
  while kill -0 "$pid" 2>/dev/null; do
    sleep 60
    local rows elapsed
    rows=$(row_count "$csv_path")
    elapsed=$(($(date +%s) - start))
    log "$label heartbeat: elapsed=${elapsed}s rows=${rows}/${expected_rows}"
    tail -n 5 "$OLLAMA_LOG" 2>/dev/null | sed 's/^/[ollama-tail] /' || true
  done
  wait "$pid"
  log "$label finished in $(($(date +%s) - start))s"
}

cd /kaggle/working/rag-hallucination-detection
mkdir -p logs/revision

section "Ollama guard"
bash scripts/kaggle_ollama_guard.sh "${MODEL}"

section "Preflight"
python -m py_compile experiments/fix_01_causal_matched_pairs.py experiments/revision_utils.py

if [ ! -s data/revision/fix_01/matched_pairs.csv ]; then
  section "Fix 1 construction"
  PYTHONUNBUFFERED=1 python -u experiments/fix_01_causal_matched_pairs.py \
    --stage construct \
    --dataset squad \
    --n_target 200 \
    --seed 42 \
    --max_contexts 400 \
    --candidate_limit 400 \
    --run_tag primary_n200 \
    2>&1 | tee logs/revision/fix_01_construct_only.log
fi

run_with_heartbeat "Fix 1 generation" "data/revision/fix_01/per_query.csv" 400 \
  bash -lc 'PYTHONUNBUFFERED=1 python -u experiments/fix_01_causal_matched_pairs.py \
    --stage generate \
    --backend ollama \
    --model "'"${MODEL}"'" \
    --resume \
    --save_every 2 \
    --progress_every 10 \
    2>&1 | tee logs/revision/fix_01_generate_only.log'

section "Fix 1 analysis"
PYTHONUNBUFFERED=1 python -u experiments/fix_01_causal_matched_pairs.py \
  --stage analyze \
  2>&1 | tee logs/revision/fix_01_analyze_only.log

section "Package Fix 1 output"
rm -f /kaggle/working/fix1_outputs.zip
zip -r /kaggle/working/fix1_outputs.zip \
  data/revision/fix_01 results/revision/fix_01 logs/revision/fix_01_*
ls -lh /kaggle/working/fix1_outputs.zip
log "done"
