#!/usr/bin/env python3
"""Shared strict contracts for modern-judge providers and result records."""

from __future__ import annotations

import abc
import dataclasses
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from errors import (
    AdapterError,
    ConfigurationError,
    IntegrityError,
    ParseError,
    RoutingRejected,
)
from prompt_rendering import RenderedPrompt
from run_config import PARSER_VERSION

SCHEMA_VERSION = "2.0"
LABEL_THRESHOLDS = {"partially_supported": 0.33, "supported": 0.67}
ALLOWED_STATUSES = {
    "ok",
    "parse_error",
    "provider_error",
    "routing_rejected",
    "integrity_error",
}


def derive_label(score: float) -> str:
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise ParseError("score must be finite and in [0,1]")
    if score < LABEL_THRESHOLDS["partially_supported"]:
        return "unsupported"
    if score < LABEL_THRESHOLDS["supported"]:
        return "partially_supported"
    return "supported"


@dataclasses.dataclass(frozen=True)
class RoutingPolicy:
    requested_provider: str
    requested_model: str
    model_revision: str
    allowed_returned_models: tuple[str, ...]
    allowed_routed_via: tuple[str, ...]
    max_fallback_attempts: int = 0

    def __post_init__(self) -> None:
        if not self.requested_provider or self.requested_provider == "auto":
            raise ConfigurationError("provider must be hard-pinned and cannot be auto")
        if not self.requested_model or self.requested_model == "auto":
            raise ConfigurationError("model must be hard-pinned and cannot be auto")
        if self.requested_model not in self.allowed_returned_models:
            raise ConfigurationError("requested model must be in allowed_returned_models")
        if any(not value or value == "auto" for value in self.allowed_returned_models):
            raise ConfigurationError("returned-model allow-list contains an invalid value")
        if not self.model_revision:
            raise ConfigurationError("model revision is required")
        if not self.allowed_routed_via:
            raise ConfigurationError("allowed_routed_via cannot be empty")
        if any(not value or value == "auto" for value in self.allowed_routed_via):
            raise ConfigurationError("route allow-list contains an invalid value")
        if self.max_fallback_attempts < 0:
            raise ConfigurationError("max_fallback_attempts cannot be negative")


@dataclasses.dataclass(frozen=True)
class JudgeRequest:
    run_id: str
    row_id: str
    pair_id: str
    condition: str
    input_digest: str
    rendered_prompt: RenderedPrompt
    attempt: int
    max_attempts: int
    parser_version: str = PARSER_VERSION

    @property
    def prompt_digest(self) -> str:
        return self.rendered_prompt.digest

    @property
    def prompt_version(self) -> str:
        return self.rendered_prompt.version

    @property
    def prompt_transport(self) -> str:
        return self.rendered_prompt.transport


@dataclasses.dataclass(frozen=True)
class ProviderResponse:
    raw_output: str
    returned_model: str
    x_routed_via: str
    x_fallback_attempts: int
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    finish_reason: str = ""
    response_metadata: Mapping[str, Any] = dataclasses.field(default_factory=dict)


class ProviderAdapter(abc.ABC):
    def __init__(self, policy: RoutingPolicy) -> None:
        self.policy = policy

    @abc.abstractmethod
    def execute(self, request: JudgeRequest) -> ProviderResponse:
        """Return one exact raw provider response."""

    def validate_routing(self, response: ProviderResponse) -> None:
        if response.returned_model not in self.policy.allowed_returned_models:
            raise RoutingRejected(
                f"returned model {response.returned_model!r} is not allowed",
                response=response,
            )
        if response.x_routed_via not in self.policy.allowed_routed_via:
            raise RoutingRejected(
                f"X-Routed-Via {response.x_routed_via!r} is not allowed",
                response=response,
            )
        if (
            response.x_fallback_attempts < 0
            or response.x_fallback_attempts > self.policy.max_fallback_attempts
        ):
            raise RoutingRejected(
                "X-Fallback-Attempts exceeds the predeclared maximum",
                response=response,
            )


def parse_strict_output(raw_output: str) -> dict[str, Any]:
    if raw_output.strip() != raw_output:
        raise ParseError("leading or trailing whitespace is not allowed")
    if raw_output.startswith("```") or raw_output.endswith("```"):
        raise ParseError("markdown fences are not allowed")
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ParseError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ParseError("output must be one JSON object")
    if set(payload) != {"score", "reason"}:
        raise ParseError("output must contain exactly score and reason")
    if isinstance(payload["score"], bool) or not isinstance(payload["score"], (int, float)):
        raise ParseError("score must be numeric")
    score = float(payload["score"])
    label = derive_label(score)
    reason = payload["reason"]
    if not isinstance(reason, str) or not reason.strip():
        raise ParseError("reason must be a non-empty string")
    if len(reason.split()) > 60:
        raise ParseError("reason exceeds 60 whitespace tokens")
    return {"score": score, "derived_label": label, "reason": reason}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_result_record(
    *,
    request: JudgeRequest,
    policy: RoutingPolicy,
    started_at_utc: str,
    finished_at_utc: str,
    latency_ms: float,
    status: str,
    device_assignment: str,
    dtype: str,
    quantization: str,
    response: ProviderResponse | None = None,
    parsed_output: Mapping[str, Any] | None = None,
    error: str = "",
) -> dict[str, Any]:
    if status not in ALLOWED_STATUSES:
        raise IntegrityError(f"unsupported result status: {status}")
    terminal = status in {"ok", "routing_rejected", "integrity_error"} or (
        status in {"parse_error", "provider_error"} and request.attempt >= request.max_attempts
    )
    metadata = dict(response.response_metadata) if response else {}
    record = {
        "schema_version": SCHEMA_VERSION,
        "run_id": request.run_id,
        "row_id": request.row_id,
        "pair_id": request.pair_id,
        "condition": request.condition,
        "input_digest": request.input_digest,
        "prompt_digest": request.prompt_digest,
        "prompt_version": request.prompt_version,
        "parser_version": request.parser_version,
        "requested_provider": policy.requested_provider,
        "requested_model": policy.requested_model,
        "model_revision": policy.model_revision,
        "returned_model": response.returned_model if response else "",
        "x_routed_via": response.x_routed_via if response else "",
        "x_fallback_attempts": response.x_fallback_attempts if response else 0,
        "attempt": request.attempt,
        "max_attempts": request.max_attempts,
        "status": status,
        "raw_output": response.raw_output if response else "",
        "parsed_score": parsed_output.get("score") if parsed_output else None,
        "derived_label": parsed_output.get("derived_label") if parsed_output else None,
        "reason": parsed_output.get("reason", "") if parsed_output else "",
        "error": error,
        "prompt_tokens": response.prompt_tokens if response else None,
        "output_tokens": response.output_tokens if response else None,
        "finish_reason": response.finish_reason if response else "",
        "started_at_utc": started_at_utc,
        "finished_at_utc": finished_at_utc,
        "latency_ms": round(float(latency_ms), 3),
        "device_assignment": device_assignment,
        "dtype": dtype,
        "quantization": quantization,
        "prompt_transport": request.prompt_transport,
        "terminal": terminal,
        "generation_metadata": metadata,
    }
    validate_record_shape(record)
    return record


def validate_record_shape(record: Mapping[str, Any]) -> None:
    schema_path = Path(__file__).with_name("OUTPUT_SCHEMA.json")
    try:
        import jsonschema
    except ImportError as exc:
        raise ConfigurationError("jsonschema is required for result validation") from exc
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        jsonschema.Draft202012Validator(schema).validate(dict(record))
    except jsonschema.ValidationError as exc:
        raise IntegrityError(f"record violates OUTPUT_SCHEMA.json: {exc.message}") from exc


__all__ = [
    "AdapterError",
    "ConfigurationError",
    "IntegrityError",
    "JudgeRequest",
    "ParseError",
    "ProviderAdapter",
    "ProviderResponse",
    "RoutingPolicy",
    "RoutingRejected",
    "derive_label",
    "make_result_record",
    "parse_strict_output",
    "utc_now",
    "validate_record_shape",
]
