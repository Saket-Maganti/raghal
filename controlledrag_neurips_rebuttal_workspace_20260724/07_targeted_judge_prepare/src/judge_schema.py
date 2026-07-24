
"""Strict modern-judge output parser."""
from __future__ import annotations
import json

EXPECTED_KEYS = {"faithfulness_score", "faithful", "insufficient_information"}

def parse_judge_output(raw: str) -> tuple[dict | None, str]:
    if not isinstance(raw, str):
        return None, "raw_output_not_string"
    if "```" in raw:
        return None, "markdown_fence"
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None, "invalid_json"
    if not isinstance(value, dict):
        return None, "not_object"
    if set(value) != EXPECTED_KEYS:
        return None, "schema_keys"
    score = value["faithfulness_score"]
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        return None, "score_range_or_type"
    if not isinstance(value["faithful"], bool) or not isinstance(
        value["insufficient_information"], bool
    ):
        return None, "boolean_type"
    if value["faithful"] != (score >= 50):
        return None, "threshold_inconsistency"
    return value, ""
