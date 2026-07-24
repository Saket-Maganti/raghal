#!/usr/bin/env python3
"""Lazy Hugging Face adapter; model loading is impossible unless explicitly enabled."""

from __future__ import annotations

from typing import Any

from provider_adapter import (
    AdapterError,
    JudgeRequest,
    ProviderAdapter,
    ProviderResponse,
    RoutingPolicy,
)

ALLOWED_QUANTIZATION = {"none", "4bit", "8bit"}
ALLOWED_DTYPES = {"bf16", "fp16", "fp32"}
ALLOWED_GPU_STRATEGIES = {"one_worker_per_gpu", "device_map_auto", "cpu"}


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
        quantization: str = "none",
        dtype: str = "bf16",
        gpu_strategy: str = "one_worker_per_gpu",
        device_index: int = 0,
        local_files_only: bool = True,
        allow_model_load: bool = False,
    ) -> None:
        super().__init__(policy)
        if not revision or revision == "main":
            raise ValueError("pin an immutable Hugging Face revision, not main")
        pinned_name = f"{model_id}@{revision}"
        if policy.requested_model != pinned_name:
            raise ValueError("policy requested_model must equal model_id@revision")
        if quantization not in ALLOWED_QUANTIZATION:
            raise ValueError(f"unsupported quantization: {quantization}")
        if dtype not in ALLOWED_DTYPES:
            raise ValueError(f"unsupported dtype: {dtype}")
        if gpu_strategy not in ALLOWED_GPU_STRATEGIES:
            raise ValueError(f"unsupported GPU strategy: {gpu_strategy}")
        self.model_id = model_id
        self.revision = revision
        self.quantization = quantization
        self.dtype = dtype
        self.gpu_strategy = gpu_strategy
        self.device_index = device_index
        self.local_files_only = local_files_only
        self.allow_model_load = allow_model_load
        self._tokenizer: Any = None
        self._model: Any = None

    def _load(self) -> None:
        if not self.allow_model_load:
            raise AdapterError(
                "model loading disabled; set allow_model_load=True explicitly"
            )
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        dtype_map = {
            "bf16": torch.bfloat16,
            "fp16": torch.float16,
            "fp32": torch.float32,
        }
        kwargs: dict[str, Any] = {
            "revision": self.revision,
            "local_files_only": self.local_files_only,
            "torch_dtype": dtype_map[self.dtype],
        }
        if self.quantization == "4bit":
            kwargs["load_in_4bit"] = True
        elif self.quantization == "8bit":
            kwargs["load_in_8bit"] = True
        if self.gpu_strategy == "device_map_auto":
            kwargs["device_map"] = "auto"
        elif self.gpu_strategy == "one_worker_per_gpu":
            kwargs["device_map"] = {"": self.device_index}
        else:
            kwargs["device_map"] = {"": "cpu"}
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            revision=self.revision,
            local_files_only=self.local_files_only,
        )
        self._model = AutoModelForCausalLM.from_pretrained(self.model_id, **kwargs)

    def execute(self, request: JudgeRequest) -> ProviderResponse:
        if self._model is None:
            self._load()
        import torch

        encoded = self._tokenizer(request.prompt, return_tensors="pt", truncation=True)
        model_device = next(self._model.parameters()).device
        encoded = {key: value.to(model_device) for key, value in encoded.items()}
        with torch.inference_mode():
            generated = self._model.generate(
                **encoded,
                do_sample=False,
                temperature=None,
                max_new_tokens=160,
            )
        new_tokens = generated[0, encoded["input_ids"].shape[1] :]
        raw_output = self._tokenizer.decode(new_tokens, skip_special_tokens=True)
        response = ProviderResponse(
            raw_output=raw_output,
            returned_model=f"{self.model_id}@{self.revision}",
            x_routed_via="local_huggingface",
            x_fallback_attempts=0,
            response_metadata={
                "quantization": self.quantization,
                "dtype": self.dtype,
                "gpu_strategy": self.gpu_strategy,
                "device_index": self.device_index,
            },
        )
        self.validate_routing(response)
        return response
