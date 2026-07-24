"""
Small Anthropic chat wrapper with the same `.invoke(prompt)` surface as OllamaLLM.

Used by the revision RAGAS-style judge path when the paper needs a
Claude-family judge and Groq should not be used.
Requires `ANTHROPIC_API_KEY` and the optional `anthropic` package.
"""

from __future__ import annotations

import os


class AnthropicLLM:
    def __init__(
        self,
        model: str = "claude-3-5-haiku-latest",
        temperature: float = 0.0,
        timeout: float = 120.0,
        max_tokens: int = 512,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("Install the Anthropic SDK: `pip install anthropic`.") from exc
        self._client = Anthropic(api_key=api_key, timeout=timeout)

    def invoke(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        chunks = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                chunks.append(text)
        return "\n".join(chunks)

