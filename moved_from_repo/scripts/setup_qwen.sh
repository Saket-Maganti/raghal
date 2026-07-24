#!/usr/bin/env bash
# scripts/setup_qwen.sh
# Pulls Qwen2.5-7B-Instruct into Ollama under the alias `qwen2.5` so the
# existing RAGPipeline / multidataset harness can use it identically to
# `mistral` and `llama3`.
#
# Usage:  bash scripts/setup_qwen.sh
#
# Prerequisites: Ollama installed and running.
#
# After this runs, the model is invokable as:
#   from langchain_ollama import OllamaLLM
#   OllamaLLM(model="qwen2.5", temperature=0.1)

set -euo pipefail

if ! command -v ollama >/dev/null 2>&1; then
  echo "[setup_qwen] Ollama is not installed. See https://ollama.com/download"
  exit 1
fi

# Pull the official 7B-instruct model. Qwen2.5 ships with the ChatML
# template; Ollama auto-applies the appropriate format.
echo "[setup_qwen] Pulling qwen2.5:7b-instruct ..."
ollama pull qwen2.5:7b-instruct

# Create a thin alias so the harness can address it as plain `qwen2.5`.
TMPDIR="$(mktemp -d)"
cat > "$TMPDIR/Modelfile.qwen25" <<'EOF'
FROM qwen2.5:7b-instruct
PARAMETER temperature 0.1
PARAMETER num_ctx 4096
EOF

ollama create qwen2.5 -f "$TMPDIR/Modelfile.qwen25"

echo "[setup_qwen] Done. Verify with: ollama run qwen2.5 'Hello'"
