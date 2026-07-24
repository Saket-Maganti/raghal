"""Shared helpers for frozen-audit experiment scripts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


N_BOOTSTRAP = 10_000


def ensure_dirs(*paths: str | Path) -> None:
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def bootstrap_mean_ci(
    values,
    n_resamples: int = N_BOOTSTRAP,
    seed: int = 42,
) -> Tuple[float, float, float]:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, arr.size, size=(n_resamples, arr.size))
    means = arr[idx].mean(axis=1)
    return (
        float(arr.mean()),
        float(np.quantile(means, 0.025)),
        float(np.quantile(means, 0.975)),
    )


def wilson_ci(successes: int, n: int, z: float = 1.96) -> Tuple[float, float, float]:
    if n <= 0:
        return float("nan"), float("nan"), float("nan")
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float(p), float(max(0.0, centre - half)), float(min(1.0, centre + half))


def cohens_d(values) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size < 2:
        return float("nan")
    sd = arr.std(ddof=1)
    if sd == 0:
        return float("nan")
    return float(arr.mean() / sd)


def make_llm(backend: str, model: str, temperature: float = 0.0):
    if backend == "groq":
        from src.groq_llm import GroqLLM

        return GroqLLM(model=model, temperature=temperature)
    if backend == "together":
        from src.together_llm import TogetherLLM

        return TogetherLLM(model=model, temperature=temperature)
    from langchain_ollama import OllamaLLM

    base_url = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST")
    if base_url:
        if not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"
        return OllamaLLM(model=model, temperature=temperature, base_url=base_url)
    return OllamaLLM(model=model, temperature=temperature)


def safe_read_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def write_markdown_table(path: str | Path, title: str, tables: dict[str, pd.DataFrame]) -> None:
    lines = [f"# {title}", ""]
    for name, df in tables.items():
        lines.extend([
            f"## {name}",
            "",
            df.to_markdown(index=False) if df is not None and not df.empty else "(no data yet)",
            "",
        ])
    Path(path).write_text("\n".join(lines))
