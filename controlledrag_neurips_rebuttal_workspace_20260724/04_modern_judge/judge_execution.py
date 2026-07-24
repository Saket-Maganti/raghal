"""Provider-independent per-row execution with frozen retry semantics."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from errors import ConfigurationError, IntegrityError, ParseError, RoutingRejected
from prompt_rendering import RenderedPrompt
from provider_adapter import (
    JudgeRequest,
    ProviderAdapter,
    ProviderResponse,
    RoutingPolicy,
    make_result_record,
    parse_strict_output,
    utc_now,
)
from run_state import retry_eligible, terminal_state, validate_attempt_sequence

AttemptSink = Callable[[Mapping[str, Any]], None]


def _safe_error(exc: BaseException) -> str:
    message = str(exc).replace("\n", " ").strip()
    if "Bearer " in message:
        message = message.split("Bearer ", 1)[0] + "Bearer [REDACTED]"
    return f"{type(exc).__name__}: {message}"[:2000]


def execute_row_with_retries(
    *,
    adapter: ProviderAdapter,
    policy: RoutingPolicy,
    row: Mapping[str, str],
    rendered_prompt: RenderedPrompt,
    run_id: str,
    max_attempts: int,
    existing_attempts: Sequence[Mapping[str, Any]] = (),
    attempt_sink: AttemptSink | None = None,
    device_assignment: str,
    dtype: str,
    quantization: str,
) -> list[dict[str, Any]]:
    prior = validate_attempt_sequence(existing_attempts)
    for record in prior:
        if record["run_id"] != run_id or record["row_id"] != row["row_id"]:
            raise IntegrityError("existing attempts belong to another run or row")
        if record["prompt_digest"] != rendered_prompt.digest:
            raise IntegrityError("resume prompt digest differs from frozen prompt")
        if int(record["max_attempts"]) != max_attempts:
            raise IntegrityError("resume retry budget differs from frozen maximum")
    if prior:
        last = max(prior, key=lambda item: int(item["attempt"]))
        if terminal_state(last, attempt_count=len(prior)):
            return []
        if not retry_eligible(last, attempt_count=len(prior)):
            return []
    next_attempt = len(prior) + 1
    emitted: list[dict[str, Any]] = []
    while next_attempt <= max_attempts:
        request = JudgeRequest(
            run_id=run_id,
            row_id=row["row_id"],
            pair_id=row["pair_id"],
            condition=row["condition"],
            input_digest=row["input_digest"],
            rendered_prompt=rendered_prompt,
            attempt=next_attempt,
            max_attempts=max_attempts,
        )
        started_at = utc_now()
        started_clock = time.monotonic()
        response: ProviderResponse | None = None
        parsed: Mapping[str, Any] | None = None
        status = "provider_error"
        error = ""
        try:
            response = adapter.execute(request)
            parsed = parse_strict_output(response.raw_output)
            status = "ok"
        except ParseError as exc:
            status = "parse_error"
            error = _safe_error(exc)
        except RoutingRejected as exc:
            status = "routing_rejected"
            response = exc.response
            error = _safe_error(exc)
        except IntegrityError as exc:
            status = "integrity_error"
            error = _safe_error(exc)
        except ConfigurationError:
            raise
        except Exception as exc:
            status = "provider_error"
            error = _safe_error(exc)
        record = make_result_record(
            request=request,
            policy=policy,
            started_at_utc=started_at,
            finished_at_utc=utc_now(),
            latency_ms=(time.monotonic() - started_clock) * 1000,
            status=status,
            device_assignment=device_assignment,
            dtype=(
                str(response.response_metadata.get("actual_parameter_dtype", dtype))
                if response
                else dtype
            ),
            quantization=(
                str(response.response_metadata.get("actual_quantization", quantization))
                if response
                else quantization
            ),
            response=response,
            parsed_output=parsed,
            error=error,
        )
        emitted.append(record)
        if attempt_sink is not None:
            attempt_sink(record)
        if record["terminal"]:
            break
        next_attempt += 1
    return emitted
