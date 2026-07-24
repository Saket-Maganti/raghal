#!/usr/bin/env bash
# scripts/run_all_m4.sh
# Sequential, resumable orchestrator for everything that runs on the M4 Air.
# Steps 5 (head-to-head with Self-RAG) and 6 (mechanistic) are GPU-only and
# live in scripts/kaggle_gpu_runs.py — invoke that on Kaggle separately.
#
# Each step is wrapped in a guard: if its primary output already exists the
# step is skipped, so re-running this script picks up where the last one
# stopped. To force a re-run of one step, delete its output directory.
#
# Usage:
#   bash scripts/run_all_m4.sh            # full pipeline
#   STEPS="1 2 3" bash scripts/run_all_m4.sh   # subset
#
# Prereqs (one-time): see RUNBOOK.md.

set -uo pipefail

cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
LOG_DIR="results/_orchestrator_logs"
mkdir -p "$LOG_DIR"

STEPS_TO_RUN="${STEPS:-1 2 3 4 7 8}"   # GPU steps (5, 6) are intentionally absent

stamp() { date +%Y-%m-%dT%H:%M:%S; }

run_step() {
  local id="$1"; shift
  local name="$1"; shift
  local sentinel="$1"; shift
  local cmd="$*"
  local log="$LOG_DIR/step${id}_${name}.log"

  if [[ -e "$sentinel" ]]; then
    echo "[$(stamp)] step ${id} (${name}): SKIP — sentinel exists at ${sentinel}"
    return 0
  fi

  echo "[$(stamp)] step ${id} (${name}): START → ${log}"
  echo "+ ${cmd}" | tee -a "$log"
  if eval "${cmd}" 2>&1 | tee -a "$log"; then
    echo "[$(stamp)] step ${id} (${name}): DONE"
  else
    local rc=$?
    echo "[$(stamp)] step ${id} (${name}): FAILED rc=${rc}; resume by re-running this script"
    return $rc
  fi
}

for step in $STEPS_TO_RUN; do
  case "$step" in
    1)  # adversarial coherence
        run_step 1 "adversarial" "results/adversarial/per_case.csv" \
          "$PY experiments/run_adversarial_coherence.py" || exit 1
        ;;
    2)  # NEW #8 multi-retriever ablation — the headline rebuttal table
        run_step 2 "multi_retriever" "results/multi_retriever/paradox_by_embedder.csv" \
          "$PY experiments/run_multi_retriever_ablation.py \
              --datasets squad pubmedqa \
              --embedders minilm bge-large e5-large gte-large \
              --n_questions 30" || exit 1
        ;;
    3)  # 5-dataset × 3-generator validation (FinanceBench excluded; gated)
        run_step 3 "multidataset" "results/multidataset/summary.csv" \
          "$PY experiments/run_multidataset_validation.py \
              --datasets squad pubmedqa hotpotqa triviaqa naturalqs \
              --models   mistral llama3 qwen2.5 \
              --n_questions 30" || exit 1
        ;;
    4)  # FinanceBench top-up (often gated; non-fatal if it fails)
        run_step 4 "financebench" "results/multidataset/financebench__mistral_per_query.csv" \
          "$PY experiments/run_multidataset_validation.py \
              --datasets financebench \
              --models   mistral llama3 qwen2.5 \
              --n_questions 30" || echo "[orchestrator] step 4 failed (likely gated dataset); continuing"
        ;;
    7)  # significance + paradox stats over the combined data
        rm -f results/stats/_done_after_revision   # always re-run
        run_step 7 "stats" "results/stats/_done_after_revision" \
          "$PY experiments/run_significance_tests.py && touch results/stats/_done_after_revision" || exit 1
        ;;
    8)  # ContextCoherenceBench packager
        run_step 8 "package" "release/context_coherence_bench_v1/metadata.json" \
          "$PY scripts/package_benchmark.py \
              --paradox_csv         results/multidataset/per_query.csv \
              --paradox_summary_csv results/multidataset/summary.csv \
              --adversarial_dir     data/adversarial \
              --output_dir          release/context_coherence_bench_v1" || exit 1
        ;;
    *)  echo "[orchestrator] unknown step ${step}; skipping" ;;
  esac
done

echo
echo "[$(stamp)] All requested M4 steps complete."
echo "Next: run scripts/kaggle_gpu_runs.py on Kaggle for steps 5 (head-to-head)"
echo "and 6 (mechanistic)."
