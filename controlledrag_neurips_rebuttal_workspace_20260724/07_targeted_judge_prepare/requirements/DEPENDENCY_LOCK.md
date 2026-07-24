
# Dependency lock

Exact versions are pinned in `requirements-kaggle.txt`. The compatibility
target is Python 3.10–3.12, Linux x86_64, CUDA 12.x, and NVIDIA T4. The lock
uses the mature Transformers 4 Qwen2 implementation rather than silently
accepting a future major-version migration. bitsandbytes 0.48.0 supplies NF4
4-bit CUDA kernels and requires a modern PyTorch.

Kaggle's official GPU image changes over time. The notebook records the actual
environment and stops if two T4 GPUs or the exact installed lock are absent.
Internet must be enabled for pinned package/model retrieval unless the exact
locked model snapshot is attached privately. An attached directory must
contain `MODEL_ID.txt` and `REVISION.txt` matching `MODEL_LOCK.json`; otherwise
the run stops before tokenizer or model loading. Attached-model mode never
changes the model ID or revision and never auto-selects another model.
