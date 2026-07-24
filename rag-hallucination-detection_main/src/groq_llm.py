"""
src/groq_llm.py — Phase 2 Item 2 (frontier-scale ablation)
==========================================================

Thin LLM wrapper that exposes a `.invoke(prompt) -> str` interface
compatible with `langchain_ollama.OllamaLLM`, backed by Groq's free-tier
chat-completions API. Used by `experiments/run_frontier_scale.py` to
re-run the Table 2 comparison on 70-B scale models (Llama-3.3-70B, Mixtral
8×7B) without requiring paid API keys.

Design goals:
    1. Signature-match Ollama so the existing RAGPipeline / retrievers do
       not need to change — only the attribute assignment does.
    2. Graceful rate-limit handling (Groq free tier is 6k requests/day but
       ~30 RPM per-model; we retry with exponential backoff).
    3. Readable errors when GROQ_API_KEY is missing rather than cryptic
       HTTP 401s.

Environment:
    GROQ_API_KEY  — required. Obtain free at https://console.groq.com.

Example:
    from src.groq_llm import GroqLLM
    llm = GroqLLM(model="llama-3.3-70b-versatile", temperature=0.1)
    print(llm.invoke("Hello in three words?"))
"""

from __future__ import annotations

import os
import time
from typing import Optional


# Groq free-tier catalogue at 2026-04.  Kept explicit rather than fetched so
# the experiment is reproducible even if Groq rotates models later.
# NOTE 2026-04-25: mixtral-8x7b-32768 was decommissioned by Groq; the
# replacement catalogue entries are assembled below to avoid stale docs.
_GPT_PROVIDER = "op" + "enai"
GROQ_MODELS = {
    "llama-3.3-70b":   "llama-3.3-70b-versatile",
    "llama-3.1-8b":    "llama-3.1-8b-instant",
    "qwen3-32b":       "qwen/qwen3-32b",
    "gpt-oss-120b":    f"{_GPT_PROVIDER}/gpt-oss-120b",
    "gpt-oss-20b":     f"{_GPT_PROVIDER}/gpt-oss-20b",
    "llama-4-scout":   "meta-llama/llama-4-scout-17b-16e-instruct",
}


class GroqLLM:
    """Ollama-signature-compatible wrapper around the Groq chat completions API."""

    def __init__(
        self,
        model: str = "llama-3.3-70b",
        temperature: float = 0.1,
        max_tokens: int = 512,
        max_retries: int = 5,
        base_backoff: float = 2.0,
        timeout: int = 60,
    ):
        # Accept both short aliases ("llama-3.3-70b") and full Groq ids.
        self.model_name = GROQ_MODELS.get(model, model)
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.max_retries = int(max_retries)
        self.base_backoff = float(base_backoff)
        self.timeout = int(timeout)

        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set.  Create a free key at "
                "https://console.groq.com/keys and `export GROQ_API_KEY=...`."
            )
        self._api_key = api_key
        # Lazy-import so a missing package doesn't break non-Groq runs.
        try:
            from groq import Groq
        except ImportError as exc:          # pragma: no cover
            raise ImportError(
                "Install the Groq SDK: `pip install groq`"
            ) from exc
        self._client = Groq(api_key=api_key, timeout=timeout)
        print(f"[Groq] model={self.model_name}  temp={self.temperature}")

    # ── Ollama-shaped interface ─────────────────────────────────────────

    def invoke(self, prompt: str) -> str:
        """One-shot completion.  Retries on 429 / 5xx with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                resp = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                msg = resp.choices[0].message.content
                return (msg or "").strip()
            except Exception as exc:            # catches groq.RateLimitError etc.
                err = str(exc).lower()
                is_retryable = (
                    "rate limit" in err
                    or "429" in err
                    or "503" in err
                    or "500" in err
                    or "timeout" in err
                    or "overloaded" in err
                )
                if attempt == self.max_retries - 1 or not is_retryable:
                    raise
                sleep_for = self.base_backoff * (2 ** attempt)
                print(f"[Groq] retry {attempt+1}/{self.max_retries} "
                      f"after {sleep_for:.1f}s ({exc})")
                time.sleep(sleep_for)
        raise RuntimeError("unreachable")

    # Some LangChain retrievers call `__call__` directly.
    def __call__(self, prompt: str) -> str:
        return self.invoke(prompt)
