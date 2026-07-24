
"""Validate the frozen runtime without loading a model."""
from __future__ import annotations
import argparse
import json
import platform
import sys

def inspect_environment(require_t4x2: bool = False) -> dict:
    result = {
        "python": platform.python_version(),
        "python_ok": sys.version_info >= (3, 10),
        "model_loaded": False,
    }
    try:
        import torch
        result.update(
            {
                "torch": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "gpu_count": torch.cuda.device_count(),
                "gpus": [
                    torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
                ],
            }
        )
    except ImportError:
        result.update({"torch": None, "cuda_available": False, "gpu_count": 0, "gpus": []})
    result["hardware_ok"] = (
        result["gpu_count"] == 2
        and all("T4" in name.upper() for name in result["gpus"])
        if require_t4x2
        else True
    )
    result["ok"] = result["python_ok"] and result["hardware_ok"]
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-t4x2", action="store_true")
    args = parser.parse_args()
    result = inspect_environment(args.require_t4x2)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 2)

if __name__ == "__main__":
    main()
