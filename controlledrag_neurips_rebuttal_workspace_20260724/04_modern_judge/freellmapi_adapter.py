#!/usr/bin/env python3
"""Hard-pinned FreeLLMAPI-style adapter with strict routing rejection."""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from typing import Any

from provider_adapter import (
    AdapterError,
    JudgeRequest,
    ProviderAdapter,
    ProviderResponse,
    RoutingPolicy,
)

Transport = Callable[[dict[str, Any]], tuple[dict[str, Any], dict[str, str]]]


class FreeLLMAPIAdapter(ProviderAdapter):
    def __init__(
        self,
        *,
        policy: RoutingPolicy,
        endpoint: str,
        api_token: str | None = None,
        allow_network: bool = False,
        transport: Transport | None = None,
        timeout_seconds: int = 120,
    ) -> None:
        super().__init__(policy)
        if not endpoint.startswith("https://") and transport is None:
            raise ValueError("real endpoint must use HTTPS")
        self.endpoint = endpoint
        self.api_token = api_token
        self.allow_network = allow_network
        self.transport = transport
        self.timeout_seconds = timeout_seconds

    def _network_transport(
        self, payload: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, str]]:
        if not self.allow_network:
            raise AdapterError("network disabled; set allow_network=True explicitly")
        if not self.api_token:
            raise AdapterError("runtime API token is required")
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(
            request, timeout=self.timeout_seconds
        ) as response:
            parsed = json.loads(response.read().decode("utf-8"))
            headers = {key.lower(): value for key, value in response.headers.items()}
        return parsed, headers

    def execute(self, request: JudgeRequest) -> ProviderResponse:
        payload = {
            "provider": self.policy.requested_provider,
            "model": self.policy.requested_model,
            "messages": [
                {"role": "user", "content": request.prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 160,
            "fusion": False,
        }
        transport = self.transport or self._network_transport
        body, raw_headers = transport(payload)
        headers = {key.lower(): str(value) for key, value in raw_headers.items()}
        required = ("x-routed-via", "x-fallback-attempts")
        missing = [name for name in required if name not in headers]
        if missing:
            raise AdapterError(f"missing required routing headers: {missing}")
        try:
            fallback_attempts = int(headers["x-fallback-attempts"])
        except ValueError as exc:
            raise AdapterError("X-Fallback-Attempts must be an integer") from exc
        returned_model = str(body.get("model", ""))
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise AdapterError("response has no choices")
        raw_output = str(choices[0].get("message", {}).get("content", ""))
        response = ProviderResponse(
            raw_output=raw_output,
            returned_model=returned_model,
            x_routed_via=headers["x-routed-via"],
            x_fallback_attempts=fallback_attempts,
            response_metadata={
                "request_id": headers.get("x-request-id", ""),
                "usage": body.get("usage", {}),
            },
        )
        self.validate_routing(response)
        return response
