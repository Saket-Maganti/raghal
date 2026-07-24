"""
src/generators.py
Registry of the three generators used in the multi-model validation (Item A3).

All three are 7-8B instruction-tuned models served through Ollama, so the
RAGPipeline interface is identical across them — we only need a uniform
place to record their distinct training distributions and the lineage
information that justifies the "rule-out family-specific effects" claim
in the paper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class GeneratorSpec:
    ollama_name:    str    # exact name passed to OllamaLLM(model=...)
    display_name:   str    # name used in tables/figures
    family:         str    # short family tag for stratification
    parameters:     int    # parameter count
    training_org:   str    # who trained it
    instruction_data: str  # one-line note on instruction-tuning data
    notes:          str = ""


GENERATORS: Dict[str, GeneratorSpec] = {
    "mistral": GeneratorSpec(
        ollama_name="mistral",
        display_name="Mistral-7B-Instruct",
        family="mistral",
        parameters=7_241_732_096,
        training_org="Mistral AI",
        instruction_data="Public instruction-following corpora; v0.2 update.",
        notes="Sliding-window attention; pretraining mix dominated by web data.",
    ),
    "llama3": GeneratorSpec(
        ollama_name="llama3",
        display_name="Llama-3-8B-Instruct",
        family="llama",
        parameters=8_030_261_248,
        training_org="Meta AI",
        instruction_data="Mixed SFT + DPO over instruction + safety data.",
        notes="GQA attention; pretraining mix includes substantial multilingual + code data.",
    ),
    "qwen2.5": GeneratorSpec(
        ollama_name="qwen2.5",
        display_name="Qwen2.5-7B-Instruct",
        family="qwen",
        parameters=7_615_616_512,
        training_org="Alibaba Cloud (Qwen team)",
        instruction_data="Multistage SFT + RLHF on Chinese + English instruction data.",
        notes="Distinct training distribution from the other two — major emphasis on Chinese-language and code data, distinct tokenizer vocabulary.",
    ),
}


def list_models() -> List[str]:
    return list(GENERATORS.keys())


def display_table_md() -> str:
    """Markdown summary of the three generators for inclusion in the paper."""
    lines = [
        "| Generator | Family | Params | Org | Instruction tuning |",
        "|-----------|--------|--------|-----|--------------------|",
    ]
    for spec in GENERATORS.values():
        lines.append(
            f"| {spec.display_name} | {spec.family} | "
            f"{spec.parameters/1e9:.1f}B | {spec.training_org} | {spec.instruction_data} |"
        )
    return "\n".join(lines)
