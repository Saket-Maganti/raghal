"""
scripts/smoke_test_groq.py — Path 2 prerequisite check
======================================================

A 10-second sanity check that the Groq frontier-scale path is wired up
correctly *before* the user kicks off a 45-minute experiment.  Verifies:

    1. `GROQ_API_KEY` is present in the environment.
    2. The `groq` Python SDK is installed.
    3. Each requested model alias resolves to a known Groq id and answers
       a one-sentence prompt within `--timeout` seconds.
    4. (Optional) Round-trips a tiny RAG-style prompt so the user sees the
       generation quality before paying for a long run.

Usage::

    export GROQ_API_KEY=...
    python3 scripts/smoke_test_groq.py
    python3 scripts/smoke_test_groq.py --models llama-3.3-70b mixtral-8x7b

Exit code is 0 on success, 1 on any failure — safe to chain in a shell
script ahead of `run_frontier_scale.py`::

    python3 scripts/smoke_test_groq.py && \
        python3 experiments/run_frontier_scale.py --datasets squad pubmedqa

"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)


def _check_env() -> bool:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        print("[smoke] ❌ GROQ_API_KEY is not set.")
        print("        Create a free key at https://console.groq.com/keys")
        print("        then `export GROQ_API_KEY=...` and re-run.")
        return False
    masked = f"{key[:6]}…{key[-4:]}" if len(key) > 12 else "(short)"
    print(f"[smoke] ✅ GROQ_API_KEY present ({masked})")
    return True


def _check_sdk() -> bool:
    try:
        import groq  # noqa: F401
    except ImportError:
        print("[smoke] ❌ `groq` SDK not installed.  Run: pip install groq")
        return False
    print("[smoke] ✅ groq SDK importable")
    return True


def _ping_model(alias: str, timeout: int, prompt: str) -> bool:
    from src.groq_llm import GroqLLM, GROQ_MODELS

    resolved = GROQ_MODELS.get(alias, alias)
    print(f"[smoke] → {alias}  (resolves to {resolved})")
    t0 = time.time()
    try:
        llm = GroqLLM(model=alias, max_tokens=64, timeout=timeout, max_retries=2)
        out = llm.invoke(prompt)
    except Exception as exc:
        print(f"[smoke] ❌ {alias} failed: {exc}")
        return False
    dt = time.time() - t0
    snippet = out.replace("\n", " ")[:120]
    print(f"[smoke] ✅ {alias}  {dt:.1f}s  →  {snippet}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--models", nargs="+",
        default=["llama-3.3-70b", "mixtral-8x7b"],
        help="Groq model aliases (or full ids) to ping.",
    )
    ap.add_argument(
        "--timeout", type=int, default=30,
        help="Per-call timeout in seconds.",
    )
    ap.add_argument(
        "--prompt", type=str,
        default="Reply with exactly one sentence describing why "
                "context coherence matters in retrieval-augmented generation.",
        help="Smoke prompt sent to each model.",
    )
    ap.add_argument(
        "--rag_demo", action="store_true",
        help="Also run a tiny RAG-shaped prompt so you can sanity-check "
             "answer quality before the long experiment.",
    )
    args = ap.parse_args()

    print("=" * 72)
    print("Groq frontier-scale smoke test")
    print("=" * 72)

    ok = _check_env() and _check_sdk()
    if not ok:
        return 1

    failed: List[str] = []
    for m in args.models:
        if not _ping_model(m, args.timeout, args.prompt):
            failed.append(m)

    if args.rag_demo and not failed:
        print("\n[smoke] RAG-shaped prompt:")
        rag_prompt = (
            "Context:\n"
            "Passage 1: The mitochondrion is the organelle that generates "
            "most of a cell's adenosine triphosphate (ATP).\n"
            "Passage 2: ATP is used by enzymes and structural proteins as a "
            "source of chemical energy.\n\n"
            "Question: What organelle produces ATP?\n"
            "Answer in one short sentence using only the passages above."
        )
        for m in args.models:
            _ping_model(m, args.timeout, rag_prompt)

    print()
    if failed:
        print(f"[smoke] ❌ {len(failed)} model(s) failed: {failed}")
        return 1
    print(f"[smoke] ✅ all {len(args.models)} models reachable.  "
          f"Ready to run experiments/run_frontier_scale.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
