#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-mistral}"
OLLAMA_ADDR="${OLLAMA_ADDR:-127.0.0.1:11434}"
OLLAMA_URL="http://${OLLAMA_ADDR}"
OLLAMA_LOG="${OLLAMA_LOG:-/kaggle/working/ollama.log}"

echo "[ollama-guard] model=${MODEL} addr=${OLLAMA_ADDR}"

if ! command -v zstd >/dev/null 2>&1; then
  echo "[ollama-guard] installing zstd"
  apt-get update -y
  apt-get install -y zstd curl git zip
fi

if ! command -v ollama >/dev/null 2>&1; then
  echo "[ollama-guard] installing ollama"
  curl -fsSL https://ollama.com/install.sh | sh
fi

is_live() {
  curl -fsS "${OLLAMA_URL}/api/tags" >/dev/null 2>&1
}

start_ollama() {
  mkdir -p "$(dirname "${OLLAMA_LOG}")"
  echo "[ollama-guard] starting ollama; log=${OLLAMA_LOG}"
  nohup env \
    OLLAMA_HOST="${OLLAMA_ADDR}" \
    OLLAMA_KEEP_ALIVE=-1 \
    OLLAMA_NUM_PARALLEL=1 \
    ollama serve >"${OLLAMA_LOG}" 2>&1 &
}

if ! is_live; then
  if pgrep -x ollama >/dev/null 2>&1; then
    echo "[ollama-guard] ollama process exists but API is not responding; restarting"
    pkill -x ollama || true
    sleep 3
  fi
  start_ollama
fi

for _ in $(seq 1 60); do
  if is_live; then
    break
  fi
  sleep 2
done

if ! is_live; then
  echo "[ollama-guard] ERROR: ollama API is still not responding" >&2
  echo "[ollama-guard] last log lines:" >&2
  tail -n 120 "${OLLAMA_LOG}" >&2 || true
  exit 1
fi

export OLLAMA_HOST="${OLLAMA_ADDR}"
if ! ollama show "${MODEL}" >/dev/null 2>&1; then
  echo "[ollama-guard] pulling ${MODEL}"
  ollama pull "${MODEL}"
fi

echo "[ollama-guard] available models:"
ollama list
echo "[ollama-guard] live"

