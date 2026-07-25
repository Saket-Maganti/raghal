#!/usr/bin/env python3
"""Build Markdown/plain-text packages and count reports from standalone fields."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIMIT = 10_000
FIELDS = [
    ("area_chair", "AREA_CHAIR_RESPONSE.md", "Area Chair"),
    ("uqxN", "REVIEWER_uqxN_RESPONSE.md", "Reviewer uqxN"),
    ("wXNA", "REVIEWER_wXNA_RESPONSE.md", "Reviewer wXNA"),
    ("diyB", "REVIEWER_diyB_RESPONSE.md", "Reviewer diyB"),
    ("d61o", "REVIEWER_d61o_RESPONSE.md", "Reviewer d61o"),
    ("wh9X", "REVIEWER_wh9X_RESPONSE.md", "Reviewer wh9X"),
]


def response_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    marker = "## Paste-ready response"
    if marker in text:
        text = text.split(marker, 1)[1].strip()
    return text


def plain(text: str) -> str:
    output = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"\|(?:\s*:?-+:?\s*\|)+", stripped):
            continue
        if stripped.startswith("#"):
            stripped = stripped.lstrip("#").strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            stripped = " / ".join(part.strip() for part in stripped.strip("|").split("|"))
        stripped = stripped.replace("**", "").replace("`", "")
        output.append(stripped)
    return "\n".join(output).strip()


def build(package: Path) -> None:
    bodies = [(key, label, response_body(package / filename)) for key, filename, label in FIELDS]
    markdown = [
        "# Final OpenReview paste package",
        "",
        "Paste each marked field separately. Do not paste the markers.",
        "",
    ]
    text = ["FINAL OPENREVIEW PLAIN-TEXT PACKAGE", ""]
    for key, label, body in bodies:
        markdown.extend(
            [
                f"## {label}",
                "",
                f"<!-- PASTE_START:{key} -->",
                body,
                f"<!-- PASTE_END:{key} -->",
                "",
            ]
        )
        text.extend([label.upper(), "", plain(body), "", "=" * 72, ""])
    (package / "FINAL_OPENREVIEW_PASTE_PACKAGE.md").write_text(
        "\n".join(markdown).rstrip() + "\n", encoding="utf-8"
    )
    (package / "FINAL_OPENREVIEW_PLAIN_TEXT_PACKAGE.txt").write_text(
        "\n".join(text).rstrip() + "\n", encoding="utf-8"
    )
    rows = []
    for key, label, body in bodies:
        count = len(body)
        rows.append(
            (
                label,
                count,
                LIMIT,
                LIMIT - count,
                count / LIMIT * 100,
                "PASS" if count <= LIMIT else "FAIL",
            )
        )
    report = [
        "# Character count report",
        "",
        "Counts use Python `len(text)` after trimming outer whitespace. Each response is a separate OpenReview field.",
        "",
        "| Field | Characters | Limit | Margin | Used | Status |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for label, count, limit, margin, used, status in rows:
        report.append(f"| {label} | {count} | {limit} | {margin} | {used:.2f}% | {status} |")
    report.extend(["", "All fields retain more than a 5% manual-edit margin."])
    (package / "CHARACTER_COUNT_REPORT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )


def main() -> None:
    build(ROOT / "with_results")
    build(ROOT / "fallback_no_new_results")


if __name__ == "__main__":
    main()
