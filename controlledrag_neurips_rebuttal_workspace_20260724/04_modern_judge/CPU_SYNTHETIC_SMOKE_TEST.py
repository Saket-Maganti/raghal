#!/usr/bin/env python3
"""CPU-only synthetic and mock tests. No network, model load, or real data."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from freellmapi_adapter import FreeLLMAPIAdapter
from huggingface_adapter import HuggingFaceAdapter, detect_accelerators
from provider_adapter import (
    AdapterError,
    JudgeRequest,
    ParseError,
    RoutingPolicy,
    RoutingRejected,
    make_result_record,
    parse_strict_output,
    utc_now,
)
from SAMPLE_SELECTION import CONDITIONS, SIZES, prepare_rows, select_candidate


def expect_raises(error_type: type[BaseException], function, *args, **kwargs) -> None:
    try:
        function(*args, **kwargs)
    except error_type:
        return
    raise AssertionError(f"expected {error_type.__name__}")


def synthetic_source_rows() -> list[dict[str, str]]:
    rows = []
    for query_index in range(200):
        for condition in CONDITIONS:
            rows.append(
                {
                    "question": f"Synthetic question {query_index}",
                    "ground_truth": f"Synthetic truth {query_index}",
                    "condition": condition,
                    "answer": f"Synthetic answer {query_index} {condition}",
                    "context": f"Synthetic context {query_index} {condition}",
                    "dataset": "synthetic",
                    "seed": "0",
                    "model": "mock-model",
                }
            )
    return rows


def test_selection() -> None:
    groups = prepare_rows(synthetic_source_rows())
    previous: set[str] = set()
    expected_pairs = {300: 100, 400: 133, 500: 167, 600: 200}
    for size in SIZES:
        rows = select_candidate(groups, size)
        row_ids = {row["row_id"] for row in rows}
        assert len(rows) == size == len(row_ids)
        assert previous.issubset(row_ids)
        previous = row_ids
        baseline_pairs = {r["pair_id"] for r in rows if r["condition"] == "baseline"}
        v1_pairs = {r["pair_id"] for r in rows if r["condition"] == "hcpc_v1"}
        assert len(baseline_pairs & v1_pairs) == expected_pairs[size]


def mock_transport(payload):
    assert payload["model"] == "mock-provider/mock-model@sha256:abc"
    assert payload["provider"] == "mock-provider"
    assert payload["fusion"] is False
    return (
        {
            "model": "mock-provider/mock-model@sha256:abc",
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"label":"supported","score":1.0,'
                            '"reason":"Synthetic context supports the answer."}'
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 8},
        },
        {
            "X-Routed-Via": "mock-provider",
            "X-Fallback-Attempts": "0",
            "X-Request-ID": "synthetic-request",
        },
    )


def test_adapters() -> None:
    pinned = "mock-provider/mock-model@sha256:abc"
    policy = RoutingPolicy(
        requested_provider="mock-provider",
        requested_model=pinned,
        allowed_returned_models=(pinned,),
        allowed_routed_via=("mock-provider",),
        max_fallback_attempts=0,
    )
    request = JudgeRequest(
        run_id="synthetic-smoke",
        row_id="crj_" + "a" * 24,
        input_digest="b" * 64,
        prompt="Synthetic prompt",
    )
    adapter = FreeLLMAPIAdapter(
        policy=policy,
        endpoint="mock://offline",
        transport=mock_transport,
        allow_network=False,
    )
    started = utc_now()
    response = adapter.execute(request)
    parsed = parse_strict_output(response.raw_output)
    record = make_result_record(
        request=request,
        policy=policy,
        started_at_utc=started,
        finished_at_utc=utc_now(),
        status="ok",
        response=response,
        parsed_output=parsed,
    )
    assert record["returned_model"] == pinned
    assert record["x_routed_via"] == "mock-provider"
    assert record["x_fallback_attempts"] == 0
    assert parsed["score"] == 1.0

    def unexpected_model_transport(payload):
        body, headers = mock_transport(payload)
        body["model"] = "unexpected/model"
        return body, headers

    def unexpected_route_transport(payload):
        body, headers = mock_transport(payload)
        headers["X-Routed-Via"] = "unexpected-provider"
        return body, headers

    def fallback_transport(payload):
        body, headers = mock_transport(payload)
        headers["X-Fallback-Attempts"] = "1"
        return body, headers

    for transport in (
        unexpected_model_transport,
        unexpected_route_transport,
        fallback_transport,
    ):
        rejected = FreeLLMAPIAdapter(
            policy=policy,
            endpoint="mock://offline",
            transport=transport,
        )
        expect_raises(RoutingRejected, rejected.execute, request)

    def missing_header_transport(payload):
        body, headers = mock_transport(payload)
        del headers["X-Routed-Via"]
        return body, headers

    missing_header = FreeLLMAPIAdapter(
        policy=policy,
        endpoint="mock://offline",
        transport=missing_header_transport,
    )
    expect_raises(AdapterError, missing_header.execute, request)

    hf_policy = RoutingPolicy(
        requested_provider="local_huggingface",
        requested_model="org/model@deadbeef",
        allowed_returned_models=("org/model@deadbeef",),
        allowed_routed_via=("local_huggingface",),
    )
    hf = HuggingFaceAdapter(
        policy=hf_policy,
        model_id="org/model",
        revision="deadbeef",
        gpu_strategy="cpu",
        dtype="fp32",
        allow_model_load=False,
    )
    expect_raises(AdapterError, hf.execute, request)
    topology = detect_accelerators()
    assert set(topology) == {"cuda_available", "gpu_count", "devices"}


def test_parser_and_unique_logging() -> None:
    valid = '{"label":"partially_supported","score":0.5,"reason":"Synthetic."}'
    assert parse_strict_output(valid)["score"] == 0.5
    expect_raises(ParseError, parse_strict_output, f"```json\n{valid}\n```")
    expect_raises(
        ParseError,
        parse_strict_output,
        '{"label":"supported","score":2,"reason":"Synthetic."}',
    )
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "results.jsonl"
        record = {"row_id": "crj_" + "a" * 24, "status": "ok"}
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        loaded = [json.loads(line) for line in path.read_text().splitlines()]
        assert len({item["row_id"] for item in loaded}) == len(loaded)


def main() -> None:
    test_selection()
    test_adapters()
    test_parser_and_unique_logging()
    print(
        json.dumps(
            {
                "status": "PASS",
                "mode": "synthetic_mock_only",
                "network_calls": 0,
                "model_loads": 0,
                "real_rows": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
