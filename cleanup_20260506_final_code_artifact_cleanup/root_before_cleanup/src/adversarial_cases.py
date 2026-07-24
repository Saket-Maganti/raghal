"""
src/adversarial_cases.py
Loader and validator for the adversarial coherence case set used in §7.6.

Supports four categories:
  - disjoint   : terminologically disjoint, high query-sim, low Jaccard
  - contradict : internally contradictory, high query-sim, high NLI-contradict
  - drift      : progressive topic drift, adjacent-sim high, endpoint-sim low
  - control    : coherent retrieval sets matched to the adversarial queries
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from langchain_core.documents import Document

CATEGORIES = ("disjoint", "contradict", "drift", "control")

_DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "adversarial",
)


@dataclass
class AdversarialCase:
    case_id: str
    category: str
    query: str
    corpus: str
    passages: List[Dict[str, str]]
    construction: Dict = field(default_factory=dict)
    expected: Dict = field(default_factory=dict)
    gold_context_label: str = "answerable"
    reference_answer: str = ""
    notes: str = ""
    matched_adversarial: Optional[str] = None

    def as_documents(self) -> List[Document]:
        return [
            Document(
                page_content=p["text"],
                metadata={
                    "source_id":   p.get("source_id", ""),
                    "case_id":     self.case_id,
                    "category":    self.category,
                },
            )
            for p in self.passages
        ]


def load_cases(
    category: str,
    data_dir: Optional[str] = None,
) -> List[AdversarialCase]:
    """Load all cases for a given category from data/adversarial/<category>.jsonl."""
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category {category!r}; must be one of {CATEGORIES}")
    path = os.path.join(data_dir or _DEFAULT_DATA_DIR, f"{category}.jsonl")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Adversarial case file missing: {path}")

    cases: List[AdversarialCase] = []
    with open(path, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            cases.append(
                AdversarialCase(
                    case_id=obj["case_id"],
                    category=obj["category"],
                    query=obj["query"],
                    corpus=obj.get("corpus", ""),
                    passages=obj["passages"],
                    construction=obj.get("construction", {}),
                    expected=obj.get("expected", {}),
                    gold_context_label=obj.get("gold_context_label", "answerable"),
                    reference_answer=obj.get("reference_answer", ""),
                    notes=obj.get("notes", ""),
                    matched_adversarial=obj.get("matched_adversarial"),
                )
            )
    return cases


def load_all_cases(data_dir: Optional[str] = None) -> Dict[str, List[AdversarialCase]]:
    return {cat: load_cases(cat, data_dir=data_dir) for cat in CATEGORIES}


def validate_case_set(cases: Dict[str, List[AdversarialCase]]) -> Dict[str, Dict]:
    """
    Quick structural validation: each adversarial category should have the
    same set of queries as the control category so we can match cases 1:1
    for the detection AUC analysis.
    """
    report: Dict[str, Dict] = {}
    control_queries = {c.query for c in cases.get("control", [])}
    for cat in ("disjoint", "contradict", "drift"):
        cat_queries = {c.query for c in cases.get(cat, [])}
        report[cat] = {
            "n_cases":        len(cases.get(cat, [])),
            "has_match":      len(cat_queries & control_queries),
            "missing_match":  sorted(list(cat_queries - control_queries)),
        }
    report["control"] = {"n_cases": len(cases.get("control", []))}
    return report
