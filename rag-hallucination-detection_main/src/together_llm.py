"""
Together.ai chat-completions wrapper with the same minimal `.invoke(prompt)`
surface used by LangChain OllamaLLM and the existing Groq wrapper.

Environment:
    TOGETHER_API_KEY=...

Default model for the revision reproduction:
    meta-llama/Llama-3.3-70B-Instruct-Turbo
"""

from __future__ import annotations

import os
import time
from typing import Optional

import requests


class TogetherLLM:
    def __init__(
        self,
        model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        temperature: float = 0.0,
        max_tokens: int = 512,
        timeout: int = 120,
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.timeout = int(timeout)
        self.api_key = api_key or os.environ.get("TOGETHER_API_KEY")
        if not self.api_key:
            raise RuntimeError("TOGETHER_API_KEY is required for TogetherLLM")
        self.url = "https://api.together.xyz/v1/chat/completions"

    def invoke(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        last_error: Optional[Exception] = None
        for attempt in range(4):
            try:
                resp = requests.post(
                    self.url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                if resp.status_code in (429, 500, 502, 503, 504):
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as exc:
                last_error = exc
                time.sleep(2 ** attempt)
        raise RuntimeError(f"TogetherLLM request failed: {last_error}")
