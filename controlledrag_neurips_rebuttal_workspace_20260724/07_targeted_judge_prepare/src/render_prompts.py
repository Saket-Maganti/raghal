
"""Render the two frozen scorer interfaces."""
from __future__ import annotations
from pathlib import Path

INTERFACES = ("answer_only", "context_conditioned")

def render_prompt(row: dict, interface: str, bundle_root: str | Path) -> str:
    if interface not in INTERFACES:
        raise ValueError(f"Unknown interface: {interface}")
    filename = (
        "ANSWER_ONLY_TEMPLATE.txt"
        if interface == "answer_only"
        else "CONTEXT_CONDITIONED_TEMPLATE.txt"
    )
    text = (Path(bundle_root) / "prompts" / filename).read_text(encoding="utf-8")
    text = text.replace("{{QUESTION}}", row["question"]).replace("{{ANSWER}}", row["answer"])
    if interface == "context_conditioned":
        text = text.replace("{{RETRIEVED_CONTEXT}}", row["retrieved_context"])
    if "{{" in text:
        raise ValueError("Unresolved prompt placeholder")
    return text

def normalized_symmetry(bundle_root: str | Path) -> bool:
    root = Path(bundle_root) / "prompts"
    answer = (root / "ANSWER_ONLY_TEMPLATE.txt").read_text(encoding="utf-8")
    context = (root / "CONTEXT_CONDITIONED_TEMPLATE.txt").read_text(encoding="utf-8")
    block = "<RETRIEVED_CONTEXT>\n{{RETRIEVED_CONTEXT}}\n</RETRIEVED_CONTEXT>\n"
    return context.replace(block, "") == answer
