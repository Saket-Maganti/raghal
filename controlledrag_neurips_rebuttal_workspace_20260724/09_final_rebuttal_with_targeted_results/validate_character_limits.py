#!/usr/bin/env python3
"""Validate per-review OpenReview limits and package synchronization."""

from __future__ import annotations

import re
from pathlib import Path

from build_packages import FIELDS, LIMIT, response_body

ROOT = Path(__file__).resolve().parent


def validate(package: Path) -> list[str]:
    failures = []
    packaged = (package / "FINAL_OPENREVIEW_PASTE_PACKAGE.md").read_text(encoding="utf-8")
    for key, filename, _ in FIELDS:
        body = response_body(package / filename)
        if len(body) > LIMIT:
            failures.append(f"{package.name}/{filename}: {len(body)} > {LIMIT}")
        match = re.search(
            rf"<!-- PASTE_START:{re.escape(key)} -->\n(.*?)\n<!-- PASTE_END:{re.escape(key)} -->",
            packaged,
            re.DOTALL,
        )
        if not match or match.group(1) != body:
            failures.append(f"{package.name}/{filename}: package mismatch")
    return failures


def main() -> None:
    failures = validate(ROOT / "with_results") + validate(
        ROOT / "fallback_no_new_results"
    )
    if failures:
        raise SystemExit("\n".join(failures))
    print("CHARACTER_LIMITS_PASS")
    print("MARKDOWN_PACKAGE_SYNC_PASS")


if __name__ == "__main__":
    main()
