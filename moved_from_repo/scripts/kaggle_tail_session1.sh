#!/usr/bin/env bash
set -euo pipefail

LOG="${1:-/kaggle/working/session1_live.log}"
PID_FILE="${2:-/kaggle/working/session1.pid}"
INTERVAL="${INTERVAL:-30}"

echo "[monitor] log=${LOG}"
echo "[monitor] pid_file=${PID_FILE}"

for i in $(seq 1 720); do
  echo
  echo "[monitor] tick=${i} time=$(date)"
  if [ -s "${PID_FILE}" ]; then
    pid="$(cat "${PID_FILE}" || true)"
    if [ -n "${pid}" ] && kill -0 "${pid}" >/dev/null 2>&1; then
      echo "[monitor] status=running pid=${pid}"
    else
      echo "[monitor] status=not-running pid=${pid:-unknown}"
    fi
  else
    echo "[monitor] status=no-pid-file"
  fi

  if [ -f "${LOG}" ]; then
    echo "[monitor] log_size=$(du -h "${LOG}" | awk '{print $1}')"
    tail -n 80 "${LOG}" || true
  else
    echo "[monitor] log missing"
  fi

  if [ -f /kaggle/working/revision_session1_outputs.zip ]; then
    echo "[monitor] output zip exists:"
    ls -lh /kaggle/working/revision_session1_outputs.zip
  fi

  if [ -s "${PID_FILE}" ]; then
    pid="$(cat "${PID_FILE}" || true)"
    if [ -n "${pid}" ] && ! kill -0 "${pid}" >/dev/null 2>&1; then
      echo "[monitor] process ended"
      exit 0
    fi
  fi

  sleep "${INTERVAL}"
done

