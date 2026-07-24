"""Strict validation for a later, separately authorized judge run."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from errors import ConfigurationError

PROMPT_VERSION = "controlledrag-modern-judge-prompt-v2"
PARSER_VERSION = "strict-score-json-v2"
ALLOWED_QUANTIZATION = {"none", "4bit", "8bit"}
ALLOWED_DTYPES = {"fp16", "bf16", "fp32"}
ALLOWED_GPU_STRATEGIES = {"one_worker_per_gpu", "device_map_auto", "cpu"}
ALLOWED_MODEL_SOURCE_MODES = {"offline_snapshot", "huggingface_download"}
ALLOWED_PROMPT_TRANSPORTS = {"plain_text", "chat_template"}
RETRYABLE_STATUSES = ("parse_error", "provider_error")
TERMINAL_FAILURE_STATUSES = ("routing_rejected", "integrity_error")
PLACEHOLDER_MARKERS = ("PIN_", "SET_")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConfigurationError(message)


def _is_placeholder(value: str) -> bool:
    return not value or value == "auto" or any(marker in value for marker in PLACEHOLDER_MARKERS)


def is_immutable_revision(revision: str) -> bool:
    if revision.lower() in {"main", "master", "latest", "head"}:
        return False
    return bool(
        re.fullmatch(r"[0-9a-f]{40,64}", revision)
        or re.fullmatch(r"sha256:[0-9a-f]{32,64}", revision)
    )


def validate_run_config(
    config: Mapping[str, Any], *, device_names: tuple[str, ...] = ()
) -> dict[str, Any]:
    required = {
        "schema_version",
        "run_real_inference",
        "run_id",
        "candidate_manifest",
        "candidate_manifest_sha256",
        "source_csv",
        "source_sha256",
        "execution_backend",
        "provider",
        "model",
        "model_id",
        "model_revision",
        "allowed_returned_models",
        "allowed_routed_via",
        "allow_fallback_attempts",
        "prompt_version",
        "parser_version",
        "prompt_transport",
        "label_thresholds",
        "max_attempts_per_row",
        "retryable_statuses",
        "max_parse_error_rate",
        "max_provider_error_rate",
        "max_condition_error_rate_difference",
        "min_primary_complete_pairs",
        "require_all_manifest_rows_terminal",
        "require_all_manifest_rows_ok",
        "model_source_mode",
        "model_snapshot_path",
        "local_files_only",
        "quantization",
        "dtype",
        "gpu_strategy",
        "context_length_policy",
        "model_context_window",
        "max_new_tokens",
        "do_sample",
        "temperature",
        "top_p",
        "top_k",
        "generation_seed",
        "checkpoint_every",
        "resume",
        "routing_rejection_policy",
        "output_jsonl",
        "attempt_log_jsonl",
        "checkpoint_json",
    }
    missing = sorted(required - set(config))
    _require(not missing, f"missing run-config fields: {missing}")
    normalized = dict(config)
    _require(config["schema_version"] == "2.0", "run-config schema_version must be 2.0")
    _require(config["run_real_inference"] is True, "real runner requires both real-run gates true")
    for field in ("run_id", "provider", "model", "model_id", "model_revision"):
        value = str(config[field])
        _require(not _is_placeholder(value), f"{field} must be hard-pinned and cannot be auto")
    _require(config["execution_backend"] == "huggingface", "Kaggle runner supports only huggingface backend")
    _require(config["provider"] == "local_huggingface", "Kaggle provider must be local_huggingface")
    _require(is_immutable_revision(str(config["model_revision"])), "model_revision must be immutable")
    exact_model = f"{config['model_id']}@{config['model_revision']}"
    _require(config["model"] == exact_model, "model must equal model_id@model_revision")
    _require(exact_model in config["allowed_returned_models"], "exact model must be allowed")
    _require(config["allowed_returned_models"] == [exact_model], "exactly one returned model must be allowed")
    _require(config["allowed_routed_via"] == ["local_huggingface"], "local route allow-list must be exact")
    _require(config["allow_fallback_attempts"] == 0, "fallback attempts must remain zero")
    _require(config["prompt_version"] == PROMPT_VERSION, "unexpected prompt version")
    _require(config["parser_version"] == PARSER_VERSION, "unexpected parser version")
    _require(config["prompt_transport"] in ALLOWED_PROMPT_TRANSPORTS, "invalid prompt transport")
    thresholds = config["label_thresholds"]
    _require(
        thresholds == {"partially_supported": 0.33, "supported": 0.67},
        "label thresholds must remain frozen at 0.33 and 0.67",
    )
    _require(
        isinstance(config["max_attempts_per_row"], int)
        and 1 <= config["max_attempts_per_row"] <= 10,
        "max_attempts_per_row must be an integer in [1,10]",
    )
    _require(tuple(config["retryable_statuses"]) == RETRYABLE_STATUSES, "retry statuses must be frozen")
    for field in (
        "max_parse_error_rate",
        "max_provider_error_rate",
        "max_condition_error_rate_difference",
    ):
        value = config[field]
        _require(isinstance(value, (int, float)) and 0 <= value <= 1, f"invalid {field}")
    _require(
        isinstance(config["min_primary_complete_pairs"], int)
        and config["min_primary_complete_pairs"] >= 0,
        "min_primary_complete_pairs must be non-negative",
    )
    for field in ("require_all_manifest_rows_terminal", "require_all_manifest_rows_ok"):
        _require(isinstance(config[field], bool), f"{field} must be boolean")
    _require(config["model_source_mode"] in ALLOWED_MODEL_SOURCE_MODES, "invalid model source mode")
    if config["model_source_mode"] == "offline_snapshot":
        _require(config["local_files_only"] is True, "offline snapshot requires local_files_only=true")
        _require(bool(str(config["model_snapshot_path"]).strip()), "offline snapshot path is required")
    else:
        _require(config["local_files_only"] is False, "authorized download requires local_files_only=false")
        _require(not str(config["model_snapshot_path"]).strip(), "download mode must not set snapshot path")
    _require(config["quantization"] in ALLOWED_QUANTIZATION, "invalid quantization")
    _require(config["dtype"] in ALLOWED_DTYPES, "invalid dtype")
    _require(config["gpu_strategy"] in ALLOWED_GPU_STRATEGIES, "invalid GPU strategy")
    if any("T4" in name.upper() for name in device_names):
        _require(config["dtype"] != "bf16", "BF16 is rejected on T4; freeze fp16 or fp32")
    _require(config["context_length_policy"] == "reject_if_too_long", "silent truncation is prohibited")
    _require(
        isinstance(config["model_context_window"], int)
        and config["model_context_window"] > config["max_new_tokens"] > 0,
        "model_context_window must exceed max_new_tokens",
    )
    _require(config["do_sample"] is False, "do_sample must remain false")
    _require(float(config["temperature"]) == 0.0, "temperature must remain zero")
    _require(float(config["top_p"]) == 1.0, "top_p must remain one")
    _require(int(config["top_k"]) == 0, "top_k must remain zero")
    _require(isinstance(config["generation_seed"], int), "generation_seed must be integer")
    _require(isinstance(config["checkpoint_every"], int) and config["checkpoint_every"] > 0, "invalid checkpoint cadence")
    _require(isinstance(config["resume"], bool), "resume must be boolean")
    _require(
        config["routing_rejection_policy"] == "quarantine_run_continue",
        "routing rejection policy must remain quarantine_run_continue",
    )
    for field in ("candidate_manifest", "output_jsonl", "attempt_log_jsonl", "checkpoint_json"):
        path = Path(str(config[field]))
        _require(not path.is_absolute() and ".." not in path.parts, f"{field} must be a safe relative path")
    _require(
        bool(re.fullmatch(r"[0-9a-f]{64}", str(config["candidate_manifest_sha256"]))),
        "candidate_manifest_sha256 must be frozen",
    )
    return normalized


def load_and_validate_config(
    path: Path, *, device_names: tuple[str, ...] = ()
) -> dict[str, Any]:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"cannot load run config: {exc}") from exc
    return validate_run_config(config, device_names=device_names)
