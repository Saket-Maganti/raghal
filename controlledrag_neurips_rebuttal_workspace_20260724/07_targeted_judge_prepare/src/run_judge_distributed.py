
"""Deterministic one-replica-per-GPU judge runner.

Model runtime imports occur only after two explicit authorization checks.
"""
from __future__ import annotations
import argparse
import json
import os
import random
from pathlib import Path

from judge_schema import parse_judge_output
from render_prompts import INTERFACES, render_prompt
from utils_hashing import deterministic_shard

def read_rows(root: Path) -> list[dict]:
    path = root / "manifests/all_frozen_rows.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

def build_tasks(rows: list[dict], rank: int, world_size: int = 2) -> list[tuple[dict, str]]:
    tasks = [
        (row, interface)
        for row in rows
        for interface in INTERFACES
        if deterministic_shard(row["experiment_row_id"], interface, world_size) == rank
    ]
    return sorted(tasks, key=lambda item: (item[0]["experiment_row_id"], item[1]))

def require_authorization(cli_authorized: bool) -> None:
    if not cli_authorized or os.environ.get("AUTHORIZE_REAL_INFERENCE") != "1":
        raise RuntimeError("PREPARATION_VALIDATED_REAL_INFERENCE_NOT_AUTHORIZED")

def truncate_context_to_limit(row: dict, tokenizer, root: Path, max_tokens: int) -> tuple[str, int, int, bool]:
    prompt = render_prompt(row, "context_conditioned", root)
    original = len(tokenizer.encode(prompt, add_special_tokens=False))
    if original <= max_tokens:
        return prompt, original, original, False
    context_ids = tokenizer.encode(row["retrieved_context"], add_special_tokens=False)
    lo, hi, best = 0, len(context_ids), ""
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = dict(row)
        candidate["retrieved_context"] = tokenizer.decode(context_ids[:mid], skip_special_tokens=True)
        rendered = render_prompt(candidate, "context_conditioned", root)
        size = len(tokenizer.encode(rendered, add_special_tokens=False))
        if size <= max_tokens:
            best = rendered
            lo = mid + 1
        else:
            hi = mid - 1
    if not best:
        raise RuntimeError("Question and answer alone exceed max_input_tokens")
    final = len(tokenizer.encode(best, add_special_tokens=False))
    return best, original, final, True

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--authorize-real-inference", action="store_true")
    args = parser.parse_args()
    require_authorization(args.authorize_real_inference)

    # Imports below this boundary are forbidden on the preparation-only path.
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    root = Path(args.bundle_root)
    output = Path(args.output_root)
    output.mkdir(parents=True, exist_ok=True)
    (output / "raw_outputs").mkdir(exist_ok=True)
    lock = json.loads((root / "MODEL_LOCK.json").read_text())
    config = json.loads((root / "RUN_CONFIG.json").read_text())
    rank = int(os.environ["LOCAL_RANK"])
    world_size = int(os.environ.get("WORLD_SIZE", "2"))
    if world_size != 2 or rank not in (0, 1):
        raise RuntimeError("Frozen execution requires exactly two ranks")
    torch.cuda.set_device(rank)
    if "T4" not in torch.cuda.get_device_name(rank).upper():
        raise RuntimeError("Frozen execution requires NVIDIA T4 GPUs")
    random.seed(config["seed"])
    torch.manual_seed(config["seed"])
    torch.cuda.manual_seed_all(config["seed"])

    attached = os.environ.get("ATTACHED_MODEL_PATH", "").strip()
    if attached:
        attached_root = Path(attached)
        attached_model_id = (attached_root / "MODEL_ID.txt").read_text().strip()
        attached_revision = (attached_root / "REVISION.txt").read_text().strip()
        if attached_model_id != lock["model_id"] or attached_revision != lock["revision"]:
            raise RuntimeError("Attached model identity sidecars do not match MODEL_LOCK.json")
    model_ref = attached or lock["model_id"]
    revision = None if attached else lock["revision"]
    tokenizer = AutoTokenizer.from_pretrained(
        model_ref, revision=revision, trust_remote_code=False, local_files_only=bool(attached)
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tasks = build_tasks(read_rows(root), rank, world_size)
    shard_path = output / "raw_outputs" / f"gpu{rank}.jsonl"
    seen = set()
    if shard_path.exists():
        for line in shard_path.read_text(encoding="utf-8").splitlines():
            prior = json.loads(line)
            seen.add((prior["experiment_row_id"], prior["interface"]))

    # Exact token audit and deterministic truncation happen before model
    # loading and before the first real row is scored.
    prepared = []
    for row, interface in tasks:
        if (row["experiment_row_id"], interface) in seen:
            continue
        if interface == "context_conditioned":
            prompt, original_tokens, final_tokens, truncated = truncate_context_to_limit(
                row, tokenizer, root, config["max_input_tokens"]
            )
            if truncated and row["human_label_available"]:
                raise RuntimeError("Frozen human row would require truncation")
        else:
            prompt = render_prompt(row, interface, root)
            original_tokens = len(tokenizer.encode(prompt, add_special_tokens=False))
            final_tokens = original_tokens
            truncated = False
            if final_tokens > config["max_input_tokens"]:
                raise RuntimeError("Answer-only prompt exceeds frozen token limit")
        chat = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False,
            add_generation_prompt=True,
        )
        prepared.append((row, interface, chat, original_tokens, final_tokens, truncated))

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_ref,
        revision=revision,
        trust_remote_code=False,
        quantization_config=quant,
        torch_dtype=torch.float16,
        device_map={"": rank},
        local_files_only=bool(attached),
    )
    model.eval()
    batch_size = int(config["batch_size_per_device"])
    if batch_size != 4:
        raise RuntimeError("Frozen per-device batch size must be 4")
    with shard_path.open("a", encoding="utf-8", buffering=1) as handle:
        for start in range(0, len(prepared), batch_size):
            batch = prepared[start : start + batch_size]
            inputs = tokenizer(
                [item[2] for item in batch],
                return_tensors="pt",
                add_special_tokens=False,
                padding=True,
            ).to(rank)
            with torch.inference_mode():
                generated = model.generate(
                    **inputs,
                    do_sample=False,
                    temperature=0.0,
                    top_p=1.0,
                    max_new_tokens=96,
                    use_cache=True,
                    pad_token_id=tokenizer.eos_token_id,
                )
            prompt_width = inputs["input_ids"].shape[1]
            for item, sequence in zip(batch, generated):
                row, interface, _, original_tokens, final_tokens, truncated = item
                raw = tokenizer.decode(sequence[prompt_width:], skip_special_tokens=True).strip()
                parsed, error = parse_judge_output(raw)
                record = {
                    "experiment_row_id": row["experiment_row_id"],
                    "interface": interface,
                    "model_id": lock["model_id"],
                    "model_revision": lock["revision"],
                    "raw_output": raw,
                    "parsed_output": parsed,
                    "valid": parsed is not None,
                    "error_type": error,
                    "rank": rank,
                    "original_input_tokens": original_tokens,
                    "final_input_tokens": final_tokens,
                    "context_truncated": truncated,
                }
                handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

if __name__ == "__main__":
    main()
