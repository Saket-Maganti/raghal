---
title: Coherence Paradox RAG Demo
emoji: 🧭
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
license: mit
---

# Coherence Paradox in RAG — interactive demo

Companion Space for the NeurIPS 2026 submission *"The Coherence Paradox in
Retrieval-Augmented Generation"*.

Three tabs:

1. **CCS calculator** — compute Context Coherence Score over arbitrary
   passages (CPU-only, ~1 s/query).
2. **Paradox explorer** — browse the per-(dataset, model) paradox drop,
   head-to-head retriever comparison, and the deployment Pareto frontier.
3. **About** — one-paragraph paper summary + benchmark pointer.

## Local run

```bash
pip install -r requirements.txt
python app.py
```

## Deployment to HF Spaces

Copy this directory plus a slim `results/` subset into a Space repo:

```
app.py
requirements.txt
results/multidataset/coherence_paradox.csv
results/headtohead/summary.csv
results/deployment_figure/pareto_summary.csv
results/deployment_figure/latency_vs_faith.png
```

The Space runs on the free CPU tier — no GPU or Ollama required. Only the
sentence-transformer embedder is loaded at first request.
