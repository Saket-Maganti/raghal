"""
Small OpenAI chat wrapper with the same `.invoke(prompt)` surface as OllamaLLM.

Used by the revision RAGAS-style judge path when Groq quota should be avoided.
Requires `OPENAI_API_KEY` and the optional `openai` package.
"""

from __future__ import annotations

import os


class OpenAILLM:
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        timeout: float = 120.0,
    ):
        self.model = model
        self.temperature = temperature
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the OpenAI SDK: `pip install openai`.") from exc
        self._client = OpenAI(api_key=api_key, timeout=timeout)

    def invoke(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        return response.choices[0].message.content or ""

