#!/usr/bin/env python3
"""Shared strict contracts for modern-judge providers."""

from __future__ import annotations

import abc
import dataclasses
import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"
ALLOWED_LABELS = {"supported", "partially_supported", "unsupported"}


class AdapterError(RuntimeError):
    """Base adapter error."""


class ParseError(AdapterError):
    """Raw output violates the frozen parser contract."""


class RoutingRejected(AdapterError):
    """Provider response does not match the predeclared routing policy."""


@dataclasses.dataclass(frozen=True)
class RoutingPolicy:
    requested_provider: str
    requested_model: str
    allowed_returned_models: tuple[str, ...]
    allowed_routed_via: tuple[str, ...]
    max_fallback_attempts: int = 0

    def __post_init__(self) -> None:
        if not self.requested_provider or self.requested_provider == "auto":
            raise ValueError("provider must be hard-pinned and cannot be auto")
        if not self.requested_model or self.requested_model == "auto":
            raise ValueError("model must be hard-pinned and cannot be auto")
        if self.requested_model not in self.allowed_returned_models:
            raise ValueError("requested model must be in allowed_returned_models")
        if not self.allowed_routed_via:
            raise ValueError("allowed_routed_via cannot be empty")
        if self.max_fallback_attempts < 0:
            raise ValueError("max_fallback_attempts cannot be negative")


@dataclasses.dataclass(frozen=True)
class JudgeRequest:
    run_id: str
    row_id: str
    input_digest: str
    prompt: str
    attempt: int = 1

    @property
    def prompt_digest(self) -> str:
        return hashlib.sha256(self.prompt.encode("utf-8")).hexdigest()


@dataclasses.dataclass(frozen=True)
class ProviderResponse:
    raw_output: str
    returned_model: str
    x_routed_via: str
    x_fallback_attempts: int
    response_metadata: Mapping[str, Any] = dataclasses.field(default_factory=dict)


class ProviderAdapter(abc.ABC):
    def __init__(self, policy: RoutingPolicy) -> None:
        self.policy = policy

    @abc.abstractmethod
    def execute(self, request: JudgeRequest) -> ProviderResponse:
        """Return one raw provider response."""

    def validate_routing(self, response: ProviderResponse) -> None:
        if response.returned_model not in self.policy.allowed_returned_models:
            raise RoutingRejected(
                f"returned model {response.returned_model!r} is not allowed"
            )
        if response.x_routed_via not in self.policy.allowed_routed_via:
            raise RoutingRejected(
                f"X-Routed-Via {response.x_routed_via!r} is not allowed"
            )
        if response.x_fallback_attempts > self.policy.max_fallback_attempts:
            raise RoutingRejected(
                "X-Fallback-Attempts exceeds the predeclared maximum"
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
    if set(payload) != {"label", "score", "reason"}:
        raise ParseError("output must contain exactly label, score, and reason")
    if payload["label"] not in ALLOWED_LABELS:
        raise ParseError("unknown label")
    if isinstance(payload["score"], bool) or not isinstance(
        payload["score"], (int, float)
    ):
        raise ParseError("score must be numeric")
    score = float(payload["score"])
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise ParseError("score must be finite and in [0,1]")
    reason = payload["reason"]
    if not isinstance(reason, str) or not reason.strip():
        raise ParseError("reason must be a non-empty string")
    if len(reason.split()) > 60:
        raise ParseError("reason exceeds 60 whitespace tokens")
    return {"label": payload["label"], "score": score, "reason": reason}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_result_record(
    *,
    request: JudgeRequest,
    policy: RoutingPolicy,
    started_at_utc: str,
    finished_at_utc: str,
    status: str,
    response: ProviderResponse | None = None,
    parsed_output: dict[str, Any] | None = None,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": request.run_id,
        "row_id": request.row_id,
        "input_digest": request.input_digest,
        "prompt_digest": request.prompt_digest,
        "status": status,
        "requested_provider": policy.requested_provider,
        "requested_model": policy.requested_model,
        "returned_model": response.returned_model if response else "",
        "x_routed_via": response.x_routed_via if response else "",
        "x_fallback_attempts": response.x_fallback_attempts if response else 0,
        "attempt": request.attempt,
        "raw_output": response.raw_output if response else "",
        "parsed_output": parsed_output,
        "error": error,
        "started_at_utc": started_at_utc,
        "finished_at_utc": finished_at_utc,
    }
