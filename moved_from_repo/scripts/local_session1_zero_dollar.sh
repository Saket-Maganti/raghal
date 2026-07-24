#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-mistral}"
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
OLLAMA_HOST_URL="${OLLAMA_HOST_URL:-http://127.0.0.1:11434}"
OLLAMA_LOG="${OLLAMA_LOG:-${REPO_DIR}/logs/revision/ollama_local.log}"
HEARTBEAT_SECONDS="${HEARTBEAT_SECONDS:-30}"

export OLLAMA_HOST="${OLLAMA_HOST_URL}"
export OLLAMA_LOG

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] [local-session1] $*" | tee -a "${REPO_DIR}/logs/revision/local_session1.log"; }
section() { echo; log "===== $* ====="; }

row_count() {
  local primary="$1"
  local fallback="${2:-}"
  local path="${primary}"
  if [ ! -s "${path}" ] && [ -n "${fallback}" ]; then
    path="${fallback}"
  fi
  if [ -s "${path}" ]; then
    python3 - "$path" <<'PYROW'
import pandas as pd
import sys

try:
    print(len(pd.read_csv(sys.argv[1])))
except Exception:
    print("?")
PYROW
  else
    echo 0
  fi
}

complete_pairs() {
  local path="$1"
  if [ -s "${path}" ]; then
    python3 - "$path" <<'PYPAIRS'
import pandas as pd
import sys

try:
    df = pd.read_csv(sys.argv[1])
    if {"pair_id", "set_type"}.issubset(df.columns):
        print(int(df.groupby("pair_id")["set_type"].nunique().eq(2).sum()))
    else:
        print(0)
except Exception:
    print("?")
PYPAIRS
  else
    echo 0
  fi
}

run_with_heartbeat() {
  local label="$1"
  local primary_csv="$2"
  local fallback_csv="$3"
  local expected="$4"
  shift 4

  local start pid rows pairs elapsed
  start=$(date +%s)
  section "${label}"
  "$@" &
  pid=$!

  while kill -0 "${pid}" 2>/dev/null; do
    sleep "${HEARTBEAT_SECONDS}"
    rows=$(row_count "${primary_csv}" "${fallback_csv}")
    pairs=$(complete_pairs "${primary_csv}")
    elapsed=$(($(date +%s) - start))
    log "${label} heartbeat: elapsed=${elapsed}s rows=${rows}/${expected} complete_pairs=${pairs}"
    tail -n 5 "${OLLAMA_LOG}" 2>/dev/null | sed 's/^/[ollama-tail] /' || true
  done

  wait "${pid}"
  elapsed=$(($(date +%s) - start))
  rows=$(row_count "${primary_csv}" "${fallback_csv}")
  pairs=$(complete_pairs "${primary_csv}")
  log "${label} finished: elapsed=${elapsed}s rows=${rows}/${expected} complete_pairs=${pairs}"
}

ensure_ollama() {
  section "Ollama"
  if ! command -v ollama >/dev/null 2>&1; then
    log "ERROR: ollama is not installed. Install from https://ollama.com/download and rerun."
    exit 1
  fi

  if ! curl -fsS "${OLLAMA_HOST_URL}/api/tags" >/dev/null 2>&1; then
    log "starting ollama serve at ${OLLAMA_HOST_URL}; log=${OLLAMA_LOG}"
    nohup ollama serve >"${OLLAMA_LOG}" 2>&1 &
    sleep 5
  else
    log "ollama already live at ${OLLAMA_HOST_URL}"
  fi

  for _ in $(seq 1 30); do
    if curl -fsS "${OLLAMA_HOST_URL}/api/tags" >/dev/null 2>&1; then
      log "ollama API is live"
      break
    fi
    sleep 2
  done

  if ! curl -fsS "${OLLAMA_HOST_URL}/api/tags" >/dev/null 2>&1; then
    log "ERROR: ollama API did not come up"
    tail -n 80 "${OLLAMA_LOG}" || true
    exit 1
  fi

  log "ensuring model ${MODEL} exists"
  ollama pull "${MODEL}" 2>&1 | tee -a "${REPO_DIR}/logs/revision/ollama_pull_local.log"
  ollama list | tee -a "${REPO_DIR}/logs/revision/local_session1.log"
}

cd "${REPO_DIR}"
mkdir -p logs/revision data/revision/fix_01 data/revision/fix_05 data/revision/fix_11 \
  results/revision/fix_01 results/revision/fix_05 results/revision/fix_11
: > logs/revision/local_session1.log

section "Environment"
pwd | tee -a logs/revision/local_session1.log
git log -1 --oneline | tee -a logs/revision/local_session1.log
python3 --version | tee -a logs/revision/local_session1.log
uname -a | tee -a logs/revision/local_session1.log

ensure_ollama

section "Preflight"
python3 -m py_compile \
  experiments/fix_01_causal_matched_pairs.py \
  experiments/fix_05_coherence_preserving_noise.py \
  experiments/fix_11_raptor_full_table.py \
  experiments/revision_utils.py

if [ ! -s data/revision/fix_01/matched_pairs.csv ]; then
  run_with_heartbeat "Fix 1 construction" \
    "data/revision/fix_01/matched_pairs.csv" "" 200 \
    bash -lc 'PYTHONUNBUFFERED=1 python3 -u experiments/fix_01_causal_matched_pairs.py \
      --stage construct \
      --dataset squad \
      --n_target 200 \
      --seed 42 \
      --max_contexts 400 \
      --candidate_limit 400 \
      --run_tag primary_n200 \
      2>&1 | tee logs/revision/fix_01_construct_local.log'
else
  log "Fix 1 matched pairs already exist; using data/revision/fix_01/matched_pairs.csv"
fi

run_with_heartbeat "Fix 1 generation" \
  "data/revision/fix_01/per_query.csv" "" 400 \
  bash -lc 'PYTHONUNBUFFERED=1 python3 -u experiments/fix_01_causal_matched_pairs.py \
    --stage generate \
    --backend ollama \
    --model "'"${MODEL}"'" \
    --resume \
    --save_every 2 \
    --progress_every 5 \
    2>&1 | tee logs/revision/fix_01_generate_local.log'

section "Fix 1 analysis"
PYTHONUNBUFFERED=1 python3 -u experiments/fix_01_causal_matched_pairs.py \
  --stage analyze \
  2>&1 | tee logs/revision/fix_01_analyze_local.log

run_with_heartbeat "Fix 5 coherence-preserving noise" \
  "data/revision/fix_05/per_query.csv" "data/revision/fix_05/per_query_partial.csv" 1600 \
  bash -lc 'PYTHONUNBUFFERED=1 python3 -u experiments/fix_05_coherence_preserving_noise.py \
    --n 200 \
    --seed 42 \
    --backend ollama \
    --model "'"${MODEL}"'" \
    --max_contexts 300 \
    --n_noise 1 2 3 \
    --save_every 10 \
    2>&1 | tee logs/revision/fix_05_local.log'

run_with_heartbeat "Fix 11 RAPTOR full table" \
  "data/revision/fix_11/per_query.csv" "" 300 \
  bash -lc 'PYTHONUNBUFFERED=1 python3 -u experiments/fix_11_raptor_full_table.py \
    --datasets squad pubmedqa hotpotqa \
    --n 100 \
    --backend ollama \
    --model "'"${MODEL}"'" \
    --max_contexts 150 \
    --raptor_clusters 6 \
    2>&1 | tee logs/revision/fix_11_local.log'

section "Package"
rm -f revision_session1_local_outputs.zip
zip -r revision_session1_local_outputs.zip \
  data/revision/fix_01 data/revision/fix_05 data/revision/fix_11 \
  results/revision/fix_01 results/revision/fix_05 results/revision/fix_11 \
  logs/revision/fix_01_* logs/revision/fix_05_local.log logs/revision/fix_11_local.log \
  logs/revision/local_session1.log logs/revision/ollama_pull_local.log
ls -lh revision_session1_local_outputs.zip | tee -a logs/revision/local_session1.log
log "Session 1 complete"
