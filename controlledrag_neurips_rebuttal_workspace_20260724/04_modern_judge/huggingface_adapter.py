#!/usr/bin/env python3
"""Guarded Hugging Face adapter with explicit source and length policies."""

from __future__ import annotations

import importlib.metadata
from pathlib import Path
from typing import Any

from errors import AdapterError, ConfigurationError, IntegrityError
from provider_adapter import (
    JudgeRequest,
    ProviderAdapter,
    ProviderResponse,
    RoutingPolicy,
)
from run_config import (
    ALLOWED_DTYPES,
    ALLOWED_GPU_STRATEGIES,
    ALLOWED_MODEL_SOURCE_MODES,
    ALLOWED_PROMPT_TRANSPORTS,
    ALLOWED_QUANTIZATION,
    is_immutable_revision,
)


def detect_accelerators() -> dict[str, Any]:
    try:
        import torch
    except ImportError:
        return {"cuda_available": False, "gpu_count": 0, "devices": []}
    count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    devices = []
    for index in range(count):
        properties = torch.cuda.get_device_properties(index)
        devices.append(
            {
                "index": index,
                "name": properties.name,
                "total_memory_bytes": properties.total_memory,
                "bf16_supported": bool(torch.cuda.is_bf16_supported()),
            }
        )
    return {"cuda_available": count > 0, "gpu_count": count, "devices": devices}


class HuggingFaceAdapter(ProviderAdapter):
    def __init__(
        self,
        *,
        policy: RoutingPolicy,
        model_id: str,
        revision: str,
        model_source_mode: str,
        model_snapshot_path: str,
        quantization: str = "none",
        dtype: str = "fp16",
        gpu_strategy: str = "one_worker_per_gpu",
        device_index: int = 0,
        local_files_only: bool = True,
        prompt_transport: str = "plain_text",
        model_context_window: int = 4096,
        max_new_tokens: int = 160,
        generation_seed: int = 20260724,
        allow_model_load: bool = False,
    ) -> None:
        super().__init__(policy)
        if not is_immutable_revision(revision):
            raise ConfigurationError("pin an immutable Hugging Face revision")
        if policy.requested_model != f"{model_id}@{revision}":
            raise ConfigurationError("policy requested_model must equal model_id@revision")
        if model_source_mode not in ALLOWED_MODEL_SOURCE_MODES:
            raise ConfigurationError("invalid model source mode")
        if quantization not in ALLOWED_QUANTIZATION:
            raise ConfigurationError(f"unsupported quantization: {quantization}")
        if dtype not in ALLOWED_DTYPES:
            raise ConfigurationError(f"unsupported dtype: {dtype}")
        if gpu_strategy not in ALLOWED_GPU_STRATEGIES:
            raise ConfigurationError(f"unsupported GPU strategy: {gpu_strategy}")
        if prompt_transport not in ALLOWED_PROMPT_TRANSPORTS:
            raise ConfigurationError(f"unsupported prompt transport: {prompt_transport}")
        if model_source_mode == "offline_snapshot":
            if not local_files_only or not model_snapshot_path:
                raise ConfigurationError("offline snapshot requires path and local_files_only=true")
        elif local_files_only or model_snapshot_path:
            raise ConfigurationError("authorized download requires no snapshot path and local_files_only=false")
        if model_context_window <= max_new_tokens:
            raise ConfigurationError("model context window must exceed max_new_tokens")
        self.model_id = model_id
        self.revision = revision
        self.model_source_mode = model_source_mode
        self.model_snapshot_path = model_snapshot_path
        self.quantization = quantization
        self.dtype = dtype
        self.gpu_strategy = gpu_strategy
        self.device_index = device_index
        self.local_files_only = local_files_only
        self.prompt_transport = prompt_transport
        self.model_context_window = model_context_window
        self.max_new_tokens = max_new_tokens
        self.generation_seed = generation_seed
        self.allow_model_load = allow_model_load
        self._tokenizer: Any = None
        self._model: Any = None
        self._torch: Any = None
        self.actual_parameter_dtype = dtype

    def _load(self) -> None:
        if not self.allow_model_load:
            raise AdapterError("model loading disabled; set allow_model_load=True explicitly")
        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )

        topology = detect_accelerators()
        if self.dtype == "bf16" and any(
            "T4" in str(device["name"]).upper() for device in topology["devices"]
        ):
            raise ConfigurationError("BF16 is rejected on T4; use a frozen FP16/FP32 config")
        if self.model_source_mode == "offline_snapshot":
            source = Path(self.model_snapshot_path)
            if not source.exists() or not source.is_dir():
                raise ConfigurationError("offline model snapshot directory does not exist")
            load_source = str(source)
            revision_kwargs: dict[str, Any] = {}
        else:
            load_source = self.model_id
            revision_kwargs = {"revision": self.revision}
        dtype_map = {
            "bf16": torch.bfloat16,
            "fp16": torch.float16,
            "fp32": torch.float32,
        }
        kwargs: dict[str, Any] = {
            **revision_kwargs,
            "local_files_only": self.local_files_only,
            "torch_dtype": dtype_map[self.dtype],
        }
        if self.quantization == "4bit":
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=dtype_map[self.dtype],
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
        elif self.quantization == "8bit":
            kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        if self.gpu_strategy == "device_map_auto":
            kwargs["device_map"] = "auto"
        elif self.gpu_strategy == "one_worker_per_gpu":
            kwargs["device_map"] = {"": self.device_index}
        else:
            kwargs["device_map"] = {"": "cpu"}
        self._tokenizer = AutoTokenizer.from_pretrained(
            load_source,
            **revision_kwargs,
            local_files_only=self.local_files_only,
        )
        self._model = AutoModelForCausalLM.from_pretrained(load_source, **kwargs)
        if self._tokenizer.pad_token_id is None:
            if self._tokenizer.eos_token_id is None:
                raise ConfigurationError("tokenizer has neither pad nor EOS token")
            self._tokenizer.pad_token = self._tokenizer.eos_token
        parameter = next(self._model.parameters())
        dtype_name = str(parameter.dtype).replace("torch.", "")
        self.actual_parameter_dtype = {
            "float16": "fp16",
            "bfloat16": "bf16",
            "float32": "fp32",
        }.get(dtype_name, self.dtype)
        if self.quantization == "none" and self.actual_parameter_dtype != self.dtype:
            raise ConfigurationError(
                f"actual parameter dtype {self.actual_parameter_dtype} differs from frozen {self.dtype}"
            )
        self._torch = torch

    def _transport_text(self, request: JudgeRequest) -> str:
        if self.prompt_transport != request.prompt_transport:
            raise IntegrityError("request prompt transport differs from adapter config")
        if self.prompt_transport == "plain_text":
            return request.rendered_prompt.plain_text
        if not getattr(self._tokenizer, "chat_template", None):
            raise ConfigurationError("chat_template transport requires tokenizer template support")
        return self._tokenizer.apply_chat_template(
            request.rendered_prompt.messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    def execute(self, request: JudgeRequest) -> ProviderResponse:
        if self._model is None:
            self._load()
        torch = self._torch
        transport_text = self._transport_text(request)
        encoded = self._tokenizer(transport_text, return_tensors="pt", truncation=False)
        prompt_tokens = int(encoded["input_ids"].shape[1])
        runtime_limits = [self.model_context_window]
        tokenizer_limit = getattr(self._tokenizer, "model_max_length", None)
        if isinstance(tokenizer_limit, int) and tokenizer_limit < 1_000_000:
            runtime_limits.append(tokenizer_limit)
        model_limit = getattr(self._model.config, "max_position_embeddings", None)
        if isinstance(model_limit, int) and model_limit > 0:
            runtime_limits.append(model_limit)
        effective_limit = min(runtime_limits)
        if prompt_tokens + self.max_new_tokens > effective_limit:
            raise IntegrityError(
                "prompt plus max_new_tokens exceeds frozen context window; truncation rejected"
            )
        model_device = next(self._model.parameters()).device
        encoded = {key: value.to(model_device) for key, value in encoded.items()}
        torch.manual_seed(self.generation_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.generation_seed)
        with torch.inference_mode():
            generated = self._model.generate(
                **encoded,
                do_sample=False,
                max_new_tokens=self.max_new_tokens,
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
            )
        new_tokens = generated[0, prompt_tokens:]
        raw_output = self._tokenizer.decode(new_tokens, skip_special_tokens=True)
        output_tokens = int(new_tokens.shape[0])
        finish_reason = "length"
        if output_tokens and self._tokenizer.eos_token_id is not None:
            if int(new_tokens[-1]) == int(self._tokenizer.eos_token_id):
                finish_reason = "eos"
        response = ProviderResponse(
            raw_output=raw_output,
            returned_model=f"{self.model_id}@{self.revision}",
            x_routed_via="local_huggingface",
            x_fallback_attempts=0,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
            finish_reason=finish_reason,
            response_metadata={
                "model_source_mode": self.model_source_mode,
                "model_revision": self.revision,
                "actual_parameter_dtype": self.actual_parameter_dtype,
                "actual_quantization": self.quantization,
                "gpu_strategy": self.gpu_strategy,
                "device_index": self.device_index,
                "prompt_transport": self.prompt_transport,
                "effective_context_window": effective_limit,
                "context_length_policy": "reject_if_too_long",
                "do_sample": False,
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 0,
                "max_new_tokens": self.max_new_tokens,
                "generation_seed": self.generation_seed,
                "eos_token_id": self._tokenizer.eos_token_id,
                "pad_token_id": self._tokenizer.pad_token_id,
                "torch_version": torch.__version__,
                "transformers_version": importlib.metadata.version("transformers"),
                "cuda_version": torch.version.cuda or "",
            },
        )
        self.validate_routing(response)
        return response
