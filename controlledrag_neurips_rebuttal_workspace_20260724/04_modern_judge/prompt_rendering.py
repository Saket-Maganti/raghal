"""Canonical prompt-v2 rendering with deterministic data escaping."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from pathlib import Path

from errors import IntegrityError
from run_config import PROMPT_VERSION

SYSTEM_START = "<!-- CONTROLLEDRAG_SYSTEM_START -->"
SYSTEM_END = "<!-- CONTROLLEDRAG_SYSTEM_END -->"
USER_START = "<!-- CONTROLLEDRAG_USER_START -->"
USER_END = "<!-- CONTROLLEDRAG_USER_END -->"
PLACEHOLDERS = ("{{question}}", "{{context}}", "{{answer}}")


@dataclasses.dataclass(frozen=True)
class RenderedPrompt:
    version: str
    transport: str
    system_message: str
    user_message: str
    plain_text: str
    digest: str

    @property
    def messages(self) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": self.user_message},
        ]


def escape_untrusted_data(value: str) -> str:
    if not isinstance(value, str):
        raise IntegrityError("prompt data must be text")
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _extract(text: str, start: str, end: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise IntegrityError(f"template must contain exactly one {start}/{end} block")
    before, remainder = text.split(start, 1)
    body, after = remainder.split(end, 1)
    if not body.strip():
        raise IntegrityError("prompt template block cannot be empty")
    return body.strip()


def render_prompt(
    template_path: Path,
    *,
    question: str,
    context: str,
    answer: str,
    transport: str,
    expected_version: str = PROMPT_VERSION,
) -> RenderedPrompt:
    if transport not in {"plain_text", "chat_template"}:
        raise IntegrityError("invalid prompt transport")
    template = template_path.read_text(encoding="utf-8")
    version_match = re.search(r"Version:\s*`([^`]+)`", template)
    if not version_match or version_match.group(1) != expected_version:
        raise IntegrityError("template version is missing or unexpected")
    template_version = version_match.group(1)
    system = _extract(template, SYSTEM_START, SYSTEM_END)
    user = _extract(template, USER_START, USER_END)
    for placeholder in PLACEHOLDERS:
        if user.count(placeholder) != 1 or placeholder in system:
            raise IntegrityError(f"template must contain exactly one user placeholder: {placeholder}")
    replacements = {
        "{{question}}": escape_untrusted_data(question),
        "{{context}}": escape_untrusted_data(context),
        "{{answer}}": escape_untrusted_data(answer),
    }
    for placeholder, value in replacements.items():
        user = user.replace(placeholder, value)
    if re.search(r"{{[^{}]+}}", system + user):
        raise IntegrityError("unresolved prompt placeholder")
    plain_text = f"SYSTEM INSTRUCTION:\n{system}\n\nUSER EVALUATION DATA:\n{user}"
    canonical = json.dumps(
        {
            "version": template_version,
            "transport": transport,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return RenderedPrompt(
        version=template_version,
        transport=transport,
        system_message=system,
        user_message=user,
        plain_text=plain_text,
        digest=digest,
    )
