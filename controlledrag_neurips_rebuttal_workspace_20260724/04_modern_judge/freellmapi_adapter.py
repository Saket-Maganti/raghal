#!/usr/bin/env python3
"""Hard-pinned API adapter with disabled-by-default network access."""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from typing import Any

from errors import AdapterError, RoutingRejected
from provider_adapter import (
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
        max_new_tokens: int = 160,
        generation_seed: int = 20260724,
    ) -> None:
        super().__init__(policy)
        if not endpoint.startswith("https://") and transport is None:
            raise ValueError("real endpoint must use HTTPS")
        self.endpoint = endpoint
        self.api_token = api_token
        self.allow_network = allow_network
        self.transport = transport
        self.timeout_seconds = timeout_seconds
        self.max_new_tokens = max_new_tokens
        self.generation_seed = generation_seed

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
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            parsed = json.loads(response.read().decode("utf-8"))
            headers = {key.lower(): value for key, value in response.headers.items()}
        return parsed, headers

    def execute(self, request: JudgeRequest) -> ProviderResponse:
        if request.prompt_transport == "chat_template":
            messages = request.rendered_prompt.messages
        else:
            messages = [{"role": "user", "content": request.rendered_prompt.plain_text}]
        payload = {
            "provider": self.policy.requested_provider,
            "model": self.policy.requested_model,
            "messages": messages,
            "temperature": 0.0,
            "top_p": 1.0,
            "max_tokens": self.max_new_tokens,
            "seed": self.generation_seed,
            "fusion": False,
        }
        transport = self.transport or self._network_transport
        body, raw_headers = transport(payload)
        headers = {key.lower(): str(value) for key, value in raw_headers.items()}
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise AdapterError("response has no choices")
        choice = choices[0]
        raw_output = str(choice.get("message", {}).get("content", ""))
        returned_model = str(body.get("model", ""))
        route = headers.get("x-routed-via", "")
        fallback_text = headers.get("x-fallback-attempts", "")
        try:
            fallback_attempts = int(fallback_text)
            if fallback_attempts < 0:
                raise ValueError
        except ValueError:
            response = ProviderResponse(
                raw_output=raw_output,
                returned_model=returned_model,
                x_routed_via=route,
                x_fallback_attempts=0,
                finish_reason=str(choice.get("finish_reason", "")),
                response_metadata={
                    "raw_x_fallback_attempts": fallback_text,
                    "routing_metadata_valid": False,
                },
            )
            raise RoutingRejected(
                "X-Fallback-Attempts is missing, negative, or non-integer",
                response=response,
            )
        usage = body.get("usage", {})
        response = ProviderResponse(
            raw_output=raw_output,
            returned_model=returned_model,
            x_routed_via=route,
            x_fallback_attempts=fallback_attempts,
            prompt_tokens=_optional_int(usage.get("prompt_tokens")),
            output_tokens=_optional_int(usage.get("completion_tokens")),
            finish_reason=str(choice.get("finish_reason", "")),
            response_metadata={
                "request_id": headers.get("x-request-id", ""),
                "generation_seed": self.generation_seed,
                "do_sample": False,
                "temperature": 0.0,
                "top_p": 1.0,
                "max_new_tokens": self.max_new_tokens,
            },
        )
        if not route:
            raise RoutingRejected("missing X-Routed-Via", response=response)
        self.validate_routing(response)
        return response


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None
