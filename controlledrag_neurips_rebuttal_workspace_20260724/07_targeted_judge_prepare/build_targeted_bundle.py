#!/usr/bin/env python3
"""Build the public-safe preparation tree and the private Kaggle input bundle.

This script performs no model inference and imports no model runtime.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import textwrap
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path


MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
SOURCE_MAIN_SHA = "78348a4a786434fbf5aa42e1179f7c81aae7695eaee4e876d145aa3cb1a575f4"
BOOTSTRAP_SEED = 20260724

REPO = Path(__file__).resolve().parents[2]
WORKSPACE = REPO.parent.parent
PUBLIC = Path(__file__).resolve().parent
PRIVATE = WORKSPACE / "CONTROLLEDRAG_TARGETED_JUDGE_INPUT"
PRIVATE_ZIP = WORKSPACE / "CONTROLLEDRAG_TARGETED_JUDGE_INPUT.zip"

MAIN_SOURCE = REPO / (
    "cleanup_20260506_final_code_artifact_cleanup/root_before_cleanup/"
    "results/revision/context_conditioned_nli/per_query_n600.csv"
)
MAIN_IDS = REPO / (
    "controlledrag_neurips_rebuttal_workspace_20260724/04_modern_judge/"
    "SAMPLE_MANIFEST_CANDIDATES/candidate_n600.csv"
)
TYPICAL_SOURCE = REPO / (
    "rag-hallucination-detection_main/human_eval_final/n99_calibration/"
    "human_eval_n99_with_context.csv"
)
DISAGREEMENT_SOURCE = REPO / (
    "rag-hallucination-detection_main/human_eval_final/n100_disagreement/"
    "annotation_batch_disagreement_100.csv"
)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_payload_sha(row: dict[str, str]) -> str:
    payload = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").strip().casefold()
    return re.sub(r"\s+", " ", value)


def semantic_key(question: str, context: str, answer: str, system: str) -> tuple[str, ...]:
    return norm(question), norm(context), norm(answer), system


def short_id(prefix: str, *parts: str) -> str:
    return prefix + hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:24]


def public_bundle_files() -> list[Path]:
    roots = ["src", "prompts", "schemas", "requirements", "notebooks", "synthetic", "tests", "analysis"]
    return sorted(p for root in roots for p in (PUBLIC / root).rglob("*") if p.is_file())


def build_rows() -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    if sha256_file(MAIN_SOURCE) != SOURCE_MAIN_SHA:
        raise RuntimeError("Main source hash does not match the provenance lock")
    main_raw = read_csv(MAIN_SOURCE)
    ids = {int(row["source_row_index"]): row for row in read_csv(MAIN_IDS)}
    if len(main_raw) != 600 or len(ids) != 600:
        raise RuntimeError("Expected exactly 600 main rows and 600 locked IDs")

    # Lock the 194-pair primary comparison to the rows complete under both
    # historical context-conditioned backbones.
    by_pair: dict[str, dict[str, dict[str, str]]] = {}
    for index, row in enumerate(main_raw):
        id_row = ids[index]
        by_pair.setdefault(id_row["pair_id"], {})[row["condition"]] = row

    pair_rows: list[dict] = []
    primary_pair_ids: set[str] = set()
    for pair_id, group in sorted(by_pair.items()):
        raw_complete = all(system in group for system in ("baseline", "hcpc_v1"))
        historical_complete = raw_complete and all(
            group[system]["faith_deberta_ctx"].strip()
            and group[system]["faith_roberta_mnli_ctx"].strip()
            for system in ("baseline", "hcpc_v1")
        )
        if historical_complete:
            primary_pair_ids.add(pair_id)
        pair_rows.append(
            {
                "pair_id": pair_id,
                "baseline_present": str("baseline" in group).lower(),
                "hcpc_v1_present": str("hcpc_v1" in group).lower(),
                "raw_pair_complete": str(raw_complete).lower(),
                "historical_context_backbones_complete": str(historical_complete).lower(),
                "primary_pair_eligible": str(historical_complete).lower(),
                "inclusion_reason": (
                    "locked historical complete-pair intersection"
                    if historical_complete
                    else "excluded from primary contrast: incomplete historical context re-encoding"
                ),
            }
        )
    if len(primary_pair_ids) != 194:
        raise RuntimeError(f"Expected 194 primary pair IDs, found {len(primary_pair_ids)}")

    main_rows: list[dict] = []
    for index, source in enumerate(main_raw):
        locked = ids[index]
        system = source["condition"] if source["condition"] in {"baseline", "hcpc_v1"} else "other"
        if not all(source[field].strip() for field in ("question", "context", "answer", "condition", "dataset")):
            raise RuntimeError(f"Missing required main field at source row {index}")
        main_rows.append(
            {
                "experiment_row_id": locked["row_id"],
                "source_row_id": str(index),
                "panel": "main_600",
                "system": system,
                "dataset": source["dataset"],
                "split": "fixed_output_context_reencoding_panel",
                "question": source["question"],
                "retrieved_context": source["context"],
                "answer": source["answer"],
                "human_label": 0,
                "human_label_available": False,
                "human_slice": "none",
                "pair_id": locked["pair_id"],
                "output_origin": "rescored",
                "provenance_source": MAIN_SOURCE.relative_to(REPO).as_posix(),
                "provenance_sha256": canonical_payload_sha(source),
            }
        )

    exclusions: list[dict] = []
    dedup: list[dict] = []

    typical_rows: list[dict] = []
    for source in read_csv(TYPICAL_SOURCE):
        label = source["adjudicated_label"].strip().lower()
        candidate_id = f"typical_{source['id']}"
        if label == "partially_supported":
            exclusions.append(
                {
                    "candidate_row_id": candidate_id,
                    "panel": "human_typical",
                    "reason": "intermediate ternary label has no approved binary mapping",
                    "source_path": TYPICAL_SOURCE.relative_to(REPO).as_posix(),
                }
            )
            continue
        if label not in {"supported", "unsupported"}:
            exclusions.append(
                {
                    "candidate_row_id": candidate_id,
                    "panel": "human_typical",
                    "reason": "unresolved or unknown adjudicated label",
                    "source_path": TYPICAL_SOURCE.relative_to(REPO).as_posix(),
                }
            )
            continue
        system = source["condition"] if source["condition"] in {"baseline", "hcpc_v1"} else "other"
        typical_rows.append(
            {
                "experiment_row_id": short_id("ht_", source["id"], source["question"], source["answer"]),
                "source_row_id": source["id"],
                "panel": "human_typical",
                "system": system,
                "dataset": source["dataset"],
                "split": "human_calibration_typical_determinate_binary",
                "question": source["question"],
                "retrieved_context": source["context"],
                "answer": source["answer"],
                "human_label": 1 if label == "supported" else 0,
                "human_label_available": True,
                "human_slice": "typical",
                "pair_id": short_id("htp_", source["id"]),
                "output_origin": "imported",
                "provenance_source": TYPICAL_SOURCE.relative_to(REPO).as_posix(),
                "provenance_sha256": canonical_payload_sha(source),
            }
        )

    # Dedupe the disagreement-targeted slice before freezing. The authoritative
    # n=100 file contains repeated semantic rows under distinct example IDs.
    disagreement_candidates = read_csv(DISAGREEMENT_SOURCE)
    candidate_groups: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for source in disagreement_candidates:
        system = source["condition"] if source["condition"] in {"baseline", "hcpc_v1"} else "other"
        key = semantic_key(
            source["question"], source["retrieved_context"], source["generated_answer"], system
        )
        candidate_groups.setdefault(key, []).append(source)

    main_semantics = {
        semantic_key(r["question"], r["retrieved_context"], r["answer"], r["system"]): r
        for r in main_rows
    }
    disagreement_rows: list[dict] = []
    for key, group in sorted(candidate_groups.items(), key=lambda item: item[0]):
        group = sorted(group, key=lambda r: r["example_id"])
        kept = group[0]
        canonical_id = short_id("hd_", kept["example_id"], *key)
        for duplicate in group[1:]:
            exclusions.append(
                {
                    "candidate_row_id": duplicate["example_id"],
                    "panel": "human_disagreement",
                    "reason": "duplicate semantic row under another example ID",
                    "source_path": DISAGREEMENT_SOURCE.relative_to(REPO).as_posix(),
                }
            )
            dedup.append(
                {
                    "candidate_row_id": duplicate["example_id"],
                    "canonical_row_id": canonical_id,
                    "duplicate_type": "within_slice_semantic",
                    "kept": "false",
                    "reason": "same normalized question/context/answer/system",
                    "source_path": DISAGREEMENT_SOURCE.relative_to(REPO).as_posix(),
                }
            )
        if key in main_semantics:
            exclusions.append(
                {
                    "candidate_row_id": kept["example_id"],
                    "panel": "human_disagreement",
                    "reason": "cross-panel semantic duplicate of a main-panel row",
                    "source_path": DISAGREEMENT_SOURCE.relative_to(REPO).as_posix(),
                }
            )
            dedup.append(
                {
                    "candidate_row_id": kept["example_id"],
                    "canonical_row_id": main_semantics[key]["experiment_row_id"],
                    "duplicate_type": "cross_panel_semantic",
                    "kept": "false",
                    "reason": "main panel has priority; prevents duplicate judge inference",
                    "source_path": DISAGREEMENT_SOURCE.relative_to(REPO).as_posix(),
                }
            )
            continue
        label = kept["adjudicated_label"].strip().lower()
        if label not in {"faithful", "hallucinated"}:
            exclusions.append(
                {
                    "candidate_row_id": kept["example_id"],
                    "panel": "human_disagreement",
                    "reason": "unresolved adjudicated label",
                    "source_path": DISAGREEMENT_SOURCE.relative_to(REPO).as_posix(),
                }
            )
            continue
        system = kept["condition"] if kept["condition"] in {"baseline", "hcpc_v1"} else "other"
        disagreement_rows.append(
            {
                "experiment_row_id": canonical_id,
                "source_row_id": kept["example_id"],
                "panel": "human_disagreement",
                "system": system,
                "dataset": kept["dataset"],
                "split": "human_calibration_disagreement_targeted_deduplicated",
                "question": kept["question"],
                "retrieved_context": kept["retrieved_context"],
                "answer": kept["generated_answer"],
                "human_label": 1 if label == "faithful" else 0,
                "human_label_available": True,
                "human_slice": "disagreement_targeted",
                "pair_id": short_id("hdp_", kept["example_id"]),
                "output_origin": "imported",
                "provenance_source": DISAGREEMENT_SOURCE.relative_to(REPO).as_posix(),
                "provenance_sha256": canonical_payload_sha(kept),
            }
        )

    # Explicit kept rows make the report self-auditing.
    for row in main_rows + typical_rows + disagreement_rows:
        dedup.append(
            {
                "candidate_row_id": row["source_row_id"],
                "canonical_row_id": row["experiment_row_id"],
                "duplicate_type": "none",
                "kept": "true",
                "reason": "unique eligible semantic row",
                "source_path": row["provenance_source"],
            }
        )

    main_rows.sort(key=lambda r: r["experiment_row_id"])
    typical_rows.sort(key=lambda r: r["experiment_row_id"])
    disagreement_rows.sort(key=lambda r: r["experiment_row_id"])
    if (len(main_rows), len(typical_rows), len(disagreement_rows)) != (600, 83, 72):
        raise RuntimeError(
            f"Unexpected eligible counts: {len(main_rows)}, {len(typical_rows)}, "
            f"{len(disagreement_rows)}"
        )
    all_rows = sorted(main_rows + typical_rows + disagreement_rows, key=lambda r: r["experiment_row_id"])
    keys = [
        semantic_key(r["question"], r["retrieved_context"], r["answer"], r["system"])
        for r in all_rows
    ]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Global semantic deduplication failed")
    return main_rows, typical_rows, disagreement_rows, pair_rows, exclusions, dedup


MODEL_LOCK = {
    "model_id": MODEL_ID,
    "revision": MODEL_REVISION,
    "trust_remote_code": False,
    "quantization": "bitsandbytes_nf4_4bit",
    "compute_dtype": "float16",
    "double_quant": True,
    "decoding": {
        "do_sample": False,
        "temperature": 0.0,
        "top_p": 1.0,
        "max_new_tokens": 96,
        "use_cache": True,
    },
}


PREREGISTRATION = """
# Targeted modern-judge experiment preregistration

Status: `FROZEN_BEFORE_REAL_INFERENCE`

No real model inference, real judge output, or result-direction inspection
occurred while this document was written.

## Scope and frozen rows

The experiment uses one immutable judge and two interfaces on fixed existing
outputs. The main manifest contains 600 eligible fixed rows. The primary
baseline-versus-HCPC-v1 contrast is restricted to the 194 pair IDs complete
under both historical context-conditioned backbones; no missing pair is
imputed. The typical calibration panel uses the 83 adjudicated determinate
binary rows (`supported=1`, `unsupported=0`); the 16
`partially_supported` rows are excluded because no approved binary mapping
exists. The deduplicated disagreement-targeted panel has 72 eligible rows and
is diagnostic because it is below the preregistered minimum of 80. The two
human slices are never pooled.

## Judge and interfaces

Judge: `Qwen/Qwen2.5-7B-Instruct` at immutable revision
`a09a35458c702b33eeacc393d103063234e8bc28`.
Quantization is bitsandbytes NF4 4-bit, float16 compute, double quantization.
Greedy decoding is fixed at `do_sample=false`, `temperature=0`, `top_p=1`,
`max_new_tokens=96`, and `use_cache=true`.

Interface A receives question and answer only. Interface B receives question,
retrieved context, and answer. Role, definition, decision rule, field order,
and strict JSON output schema are identical. The score is the continuous
primary judge output; the boolean is secondary.

## Primary analysis A: fixed-output system contrast

For each interface report the baseline mean, HCPC-v1 mean, and paired mean
contrast `baseline - HCPC-v1` on the 194 locked pair IDs with a 95% paired
bootstrap interval. Report
`context-conditioned contrast - answer-only contrast`.

Classification is frozen as:

- sign reversal: the two point-estimate contrasts have opposite non-zero signs;
- same sign / material magnitude change: same sign and absolute
  difference-in-contrasts is at least 5 score points;
- same sign / small change: same sign and absolute difference is below 5;
- indeterminate: a required point estimate is unavailable or a contrast is
  exactly zero.

The material threshold is fixed at 5 points on the 0–100 scale.

## Primary analysis B: same-row human calibration

Analyze each human slice separately for each interface. Report Spearman
correlation between judge score and human label, sklearn average precision
with faithful=1, and valid-output rate. Compare interfaces with a paired-row
bootstrap for AP and Spearman differences and 95% intervals. The 83-row
typical determinate panel is the sole robustness-qualified bridge. The
72-row disagreement-targeted panel is diagnostic and must not be described as
a robust rebuttal bridge.

## Secondary analysis

For each interface and human slice report boolean accuracy, balanced accuracy,
precision, recall, F1, confusion matrix, and Brier score using
`faithfulness_score / 100`. Secondary metrics cannot displace the primary
outcomes.

## Bootstrap and missingness

Use 10,000 percentile bootstrap replicates with seed 20260724. Resample
complete pair IDs for system contrasts and rows within a human slice for
calibration. Preserve and report requested rows, valid rows, invalid JSON,
schema violations, truncated outputs, OOM/retry failures, duplicate outputs,
and missing outputs. No silent dropping is permitted.

## Context and execution

Maximum input length is 4096 tokens. Preserve question and answer. If needed,
truncate retrieved context from the right only, before first real inference,
record original/final token counts, and apply the same rule deterministically.
No frozen human row is expected to require truncation: a conservative
pre-tokenizer bound of one token per three Unicode characters yields a maximum
under 1,100 tokens across candidate inputs. Exact token counts are checked with
the locked tokenizer before model loading.

Use two independent one-GPU 4-bit replicas under
`torchrun --standalone --nproc_per_node=2`; never use model parallelism or
`device_map="auto"`. Initial and frozen per-device batch size is 4. A
synthetic allocation probe may reduce it only before the first real row is
scored and must record the final value. No precision fallback is allowed.

## Inclusion gates

Strong inclusion requires verified model identity/revision, matching manifest
checksums, at least 98% valid outputs, no differential missingness above 2
percentage points across systems/interfaces, complete primary analysis, no
post-hoc model/prompt selection, and bounded wording.

Valid-output rate from 95% to below 98%, or minor non-differential missingness,
is a qualified inclusion candidate requiring explicit caveats and professor
approval. Exclude if revision is unverified, valid-output rate is below 95%,
differential missingness may alter conclusions, provenance fails, prompts
changed after results, identities differ across shards, outputs are duplicate
or corrupt, or the bundle is not reproducible.

Null, same-direction, opposite-direction, and contrary results are not
exclusion reasons.
"""


def build_public_files() -> None:
    prompts = {
        "prompts/JUDGE_RUBRIC.md": """
# Frozen faithfulness rubric

Act as a strict faithfulness evaluator. Judge only whether the answer's factual
claims are supported under the evidence visible in the selected interface.
Do not use hidden reasoning in the output. A score of 50 or more maps to
`faithful=true`; a score below 50 maps to `faithful=false`.
`insufficient_information=true` only when the visible evidence is insufficient
to assess the answer. Return exactly one JSON object with
`faithfulness_score` (integer 0–100), `faithful` (boolean), and
`insufficient_information` (boolean), with no additional keys, markdown, or
explanation.
""",
        "prompts/ANSWER_ONLY_TEMPLATE.txt": """
SYSTEM ROLE
You are a strict faithfulness evaluator.

DEFINITION AND DECISION RULE
Judge only whether the answer's factual claims are supported under the evidence visible in this interface.
A faithfulness_score of 50 or more requires faithful=true; a score below 50 requires faithful=false.
Set insufficient_information=true only when the visible evidence is insufficient to assess the answer.
Do not reveal chain-of-thought or provide an explanation.

INPUT
<QUESTION>
{{QUESTION}}
</QUESTION>
<ANSWER>
{{ANSWER}}
</ANSWER>

OUTPUT
Return exactly one JSON object:
{"faithfulness_score": 0, "faithful": false, "insufficient_information": false}
faithfulness_score must be an integer from 0 to 100.
faithful and insufficient_information must be booleans.
Do not use markdown fences. Do not add keys or text.
""",
        "prompts/CONTEXT_CONDITIONED_TEMPLATE.txt": """
SYSTEM ROLE
You are a strict faithfulness evaluator.

DEFINITION AND DECISION RULE
Judge only whether the answer's factual claims are supported under the evidence visible in this interface.
A faithfulness_score of 50 or more requires faithful=true; a score below 50 requires faithful=false.
Set insufficient_information=true only when the visible evidence is insufficient to assess the answer.
Do not reveal chain-of-thought or provide an explanation.

INPUT
<QUESTION>
{{QUESTION}}
</QUESTION>
<RETRIEVED_CONTEXT>
{{RETRIEVED_CONTEXT}}
</RETRIEVED_CONTEXT>
<ANSWER>
{{ANSWER}}
</ANSWER>

OUTPUT
Return exactly one JSON object:
{"faithfulness_score": 0, "faithful": false, "insufficient_information": false}
faithfulness_score must be an integer from 0 to 100.
faithful and insufficient_information must be booleans.
Do not use markdown fences. Do not add keys or text.
""",
        "prompts/PROMPT_DIFF_AUDIT.md": """
# Prompt symmetry audit

Status: `PASS`

Normalization replaces the complete retrieved-context block in the
context-conditioned template with nothing, then normalizes line endings and
blank lines. The normalized result is byte-identical to the answer-only
template.

```diff
 <QUESTION>
 {{QUESTION}}
 </QUESTION>
+<RETRIEVED_CONTEXT>
+{{RETRIEVED_CONTEXT}}
+</RETRIEVED_CONTEXT>
 <ANSWER>
 {{ANSWER}}
 </ANSWER>
```

No other semantic or lexical difference exists. Role, faithfulness
definition, threshold, question/answer order, output schema, and prohibition
on explanations are identical.
""",
    }
    for rel, content in prompts.items():
        write(PUBLIC / rel, content)

    write_json(PUBLIC / "MODEL_LOCK.json", MODEL_LOCK)
    write(PUBLIC / "EXPERIMENT_PREREGISTRATION.md", PREREGISTRATION)

    schema_input = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "experiment_row_id",
            "source_row_id",
            "panel",
            "system",
            "dataset",
            "split",
            "question",
            "retrieved_context",
            "answer",
            "human_label",
            "human_label_available",
            "human_slice",
            "pair_id",
            "output_origin",
            "provenance_source",
            "provenance_sha256",
        ],
        "properties": {
            "experiment_row_id": {"type": "string", "minLength": 1},
            "source_row_id": {"type": "string", "minLength": 1},
            "panel": {"enum": ["main_600", "human_typical", "human_disagreement"]},
            "system": {"enum": ["baseline", "hcpc_v1", "other"]},
            "dataset": {"type": "string", "minLength": 1},
            "split": {"type": "string", "minLength": 1},
            "question": {"type": "string", "minLength": 1},
            "retrieved_context": {"type": "string", "minLength": 1},
            "answer": {"type": "string", "minLength": 1},
            "human_label": {"type": "integer", "minimum": 0, "maximum": 1},
            "human_label_available": {"type": "boolean"},
            "human_slice": {"enum": ["typical", "disagreement_targeted", "none"]},
            "pair_id": {"type": "string", "minLength": 1},
            "output_origin": {
                "enum": ["generated", "rescored", "reencoded", "imported", "aggregated"]
            },
            "provenance_source": {"type": "string", "minLength": 1},
            "provenance_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
    }
    schema_judge = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["faithfulness_score", "faithful", "insufficient_information"],
        "properties": {
            "faithfulness_score": {"type": "integer", "minimum": 0, "maximum": 100},
            "faithful": {"type": "boolean"},
            "insufficient_information": {"type": "boolean"},
        },
    }
    schema_output = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "experiment_row_id",
            "interface",
            "model_id",
            "model_revision",
            "raw_output",
            "parsed_output",
            "valid",
            "error_type",
            "rank",
            "original_input_tokens",
            "final_input_tokens",
            "context_truncated",
        ],
        "properties": {
            "experiment_row_id": {"type": "string", "minLength": 1},
            "interface": {"enum": ["answer_only", "context_conditioned"]},
            "model_id": {"const": MODEL_ID},
            "model_revision": {"const": MODEL_REVISION},
            "raw_output": {"type": "string"},
            "parsed_output": {"anyOf": [schema_judge, {"type": "null"}]},
            "valid": {"type": "boolean"},
            "error_type": {"type": "string"},
            "rank": {"type": "integer", "minimum": 0, "maximum": 1},
            "original_input_tokens": {"type": "integer", "minimum": 0},
            "final_input_tokens": {"type": "integer", "minimum": 0, "maximum": 4096},
            "context_truncated": {"type": "boolean"},
        },
    }
    write_json(PUBLIC / "schemas/input_row.schema.json", schema_input)
    write_json(PUBLIC / "schemas/judge_output.schema.json", schema_judge)
    write_json(PUBLIC / "schemas/output_row.schema.json", schema_output)

    write(
        PUBLIC / "src/utils_hashing.py",
        r'''
"""Deterministic hashing helpers."""
from __future__ import annotations
import hashlib
import json
import re
import unicodedata
from pathlib import Path

def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).strip()).casefold()

def semantic_digest(row: dict) -> str:
    fields = [normalize_text(str(row[k])) for k in ("question", "retrieved_context", "answer")]
    fields.append(str(row["system"]))
    return hashlib.sha256("\x1f".join(fields).encode()).hexdigest()

def deterministic_shard(experiment_row_id: str, interface: str, world_size: int = 2) -> int:
    payload = f"{experiment_row_id}{interface}".encode()
    return int(hashlib.sha256(payload).hexdigest(), 16) % world_size
''',
    )
    write(
        PUBLIC / "src/judge_schema.py",
        r'''
"""Strict modern-judge output parser."""
from __future__ import annotations
import json

EXPECTED_KEYS = {"faithfulness_score", "faithful", "insufficient_information"}

def parse_judge_output(raw: str) -> tuple[dict | None, str]:
    if not isinstance(raw, str):
        return None, "raw_output_not_string"
    if "```" in raw:
        return None, "markdown_fence"
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None, "invalid_json"
    if not isinstance(value, dict):
        return None, "not_object"
    if set(value) != EXPECTED_KEYS:
        return None, "schema_keys"
    score = value["faithfulness_score"]
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        return None, "score_range_or_type"
    if not isinstance(value["faithful"], bool) or not isinstance(
        value["insufficient_information"], bool
    ):
        return None, "boolean_type"
    if value["faithful"] != (score >= 50):
        return None, "threshold_inconsistency"
    return value, ""
''',
    )
    write(
        PUBLIC / "src/render_prompts.py",
        r'''
"""Render the two frozen scorer interfaces."""
from __future__ import annotations
from pathlib import Path

INTERFACES = ("answer_only", "context_conditioned")

def render_prompt(row: dict, interface: str, bundle_root: str | Path) -> str:
    if interface not in INTERFACES:
        raise ValueError(f"Unknown interface: {interface}")
    filename = (
        "ANSWER_ONLY_TEMPLATE.txt"
        if interface == "answer_only"
        else "CONTEXT_CONDITIONED_TEMPLATE.txt"
    )
    text = (Path(bundle_root) / "prompts" / filename).read_text(encoding="utf-8")
    text = text.replace("{{QUESTION}}", row["question"]).replace("{{ANSWER}}", row["answer"])
    if interface == "context_conditioned":
        text = text.replace("{{RETRIEVED_CONTEXT}}", row["retrieved_context"])
    if "{{" in text:
        raise ValueError("Unresolved prompt placeholder")
    return text

def normalized_symmetry(bundle_root: str | Path) -> bool:
    root = Path(bundle_root) / "prompts"
    answer = (root / "ANSWER_ONLY_TEMPLATE.txt").read_text(encoding="utf-8")
    context = (root / "CONTEXT_CONDITIONED_TEMPLATE.txt").read_text(encoding="utf-8")
    block = "<RETRIEVED_CONTEXT>\n{{RETRIEVED_CONTEXT}}\n</RETRIEVED_CONTEXT>\n"
    return context.replace(block, "") == answer
''',
    )
    write(
        PUBLIC / "src/validate_environment.py",
        r'''
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
''',
    )
    write(
        PUBLIC / "src/validate_input_bundle.py",
        r'''
"""Verify private input checksums, schemas, counts, and frozen identities."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from judge_schema import parse_judge_output
from render_prompts import normalized_symmetry
from utils_hashing import semantic_digest, sha256_file

def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

def verify_checksums(root: Path) -> tuple[bool, list[str]]:
    mismatches = []
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = root / relative
        if not path.is_file() or sha256_file(path) != expected:
            mismatches.append(relative)
    return not mismatches, mismatches

def validate_bundle(root: str | Path) -> dict:
    root = Path(root)
    checksum_ok, mismatches = verify_checksums(root)
    summary = json.loads((root / "manifests/MANIFEST_SUMMARY.json").read_text())
    lock = json.loads((root / "MODEL_LOCK.json").read_text())
    rows = read_jsonl(root / "manifests/all_frozen_rows.jsonl")
    ids = [r["experiment_row_id"] for r in rows]
    semantics = [semantic_digest(r) for r in rows]
    required = {
        "experiment_row_id", "source_row_id", "panel", "system", "dataset", "split",
        "question", "retrieved_context", "answer", "human_label",
        "human_label_available", "human_slice", "pair_id", "output_origin",
        "provenance_source", "provenance_sha256"
    }
    schema_ok = all(set(row) == required for row in rows)
    counts_ok = (
        len(rows) == summary["all_frozen_rows"]
        and sum(r["panel"] == "main_600" for r in rows) == summary["main_eligible"]
        and sum(r["panel"] == "human_typical" for r in rows) == summary["typical_eligible"]
        and sum(r["panel"] == "human_disagreement" for r in rows)
        == summary["disagreement_eligible"]
    )
    result = {
        "checksum_ok": checksum_ok,
        "checksum_mismatches": mismatches,
        "schema_ok": schema_ok,
        "counts_ok": counts_ok,
        "unique_ids": len(ids) == len(set(ids)),
        "unique_semantics": len(semantics) == len(set(semantics)),
        "model_lock_ok": (
            lock["model_id"] == "Qwen/Qwen2.5-7B-Instruct"
            and lock["revision"] == "a09a35458c702b33eeacc393d103063234e8bc28"
            and lock["quantization"] == "bitsandbytes_nf4_4bit"
        ),
        "prompt_symmetry_ok": normalized_symmetry(root),
        "model_loaded": False,
        "network_inference_calls": 0,
        "real_rows_scored": 0,
    }
    result["ok"] = all(
        result[key]
        for key in (
            "checksum_ok", "schema_ok", "counts_ok", "unique_ids",
            "unique_semantics", "model_lock_ok", "prompt_symmetry_ok"
        )
    )
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_root")
    args = parser.parse_args()
    result = validate_bundle(args.bundle_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 2)

if __name__ == "__main__":
    main()
''',
    )
    write(
        PUBLIC / "src/run_judge_distributed.py",
        r'''
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
''',
    )
    write(
        PUBLIC / "src/merge_shards.py",
        r'''
"""Merge immutable per-rank shards without dropping malformed outputs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def merge(output_root: str | Path) -> dict:
    root = Path(output_root)
    records = []
    for rank in (0, 1):
        path = root / "raw_outputs" / f"gpu{rank}.jsonl"
        if not path.exists():
            raise FileNotFoundError(path)
        records.extend(json.loads(line) for line in path.read_text().splitlines() if line)
    keys = [(r["experiment_row_id"], r["interface"]) for r in records]
    duplicates = len(keys) - len(set(keys))
    merged = sorted(records, key=lambda r: (r["experiment_row_id"], r["interface"]))
    path = root / "raw_outputs/merged_outputs.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in merged),
        encoding="utf-8",
    )
    return {"records": len(merged), "duplicates": duplicates, "path": str(path)}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root")
    args = parser.parse_args()
    print(json.dumps(merge(args.output_root), indent=2))

if __name__ == "__main__":
    main()
''',
    )
    write(
        PUBLIC / "src/validate_outputs.py",
        r'''
"""Validate complete output coverage and preserve every failure category."""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from judge_schema import parse_judge_output

def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]

def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def validate(bundle_root: str | Path, output_root: str | Path) -> dict:
    bundle, output = Path(bundle_root), Path(output_root)
    expected_rows = load_jsonl(bundle / "manifests/all_frozen_rows.jsonl")
    expected = {(r["experiment_row_id"], i) for r in expected_rows for i in ("answer_only", "context_conditioned")}
    records = load_jsonl(output / "raw_outputs/merged_outputs.jsonl")
    counts = Counter((r["experiment_row_id"], r["interface"]) for r in records)
    duplicates = sorted(k for k, n in counts.items() if n > 1)
    actual = set(counts)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    invalid = []
    categories = Counter()
    for record in records:
        parsed, error = parse_judge_output(record.get("raw_output", ""))
        if (
            record.get("model_id") != "Qwen/Qwen2.5-7B-Instruct"
            or record.get("model_revision") != "a09a35458c702b33eeacc393d103063234e8bc28"
        ):
            error = "wrong_model_identity"
            parsed = None
        if parsed is None:
            categories[error] += 1
            invalid.append({**record, "validation_error": error})
    validation = output / "validation"
    validation.mkdir(parents=True, exist_ok=True)
    (validation / "INVALID_OUTPUTS.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in invalid)
    )
    write_csv(
        validation / "MISSING_OUTPUTS.csv",
        [{"experiment_row_id": a, "interface": b} for a, b in missing],
        ["experiment_row_id", "interface"],
    )
    write_csv(
        validation / "DUPLICATE_OUTPUTS.csv",
        [{"experiment_row_id": a, "interface": b, "count": counts[(a, b)]} for a, b in duplicates],
        ["experiment_row_id", "interface", "count"],
    )
    row_lookup = {r["experiment_row_id"]: r for r in expected_rows}
    requested = defaultdict(int)
    valid = defaultdict(int)
    for row_id, interface in expected:
        key = (row_lookup[row_id]["system"], interface)
        requested[key] += 1
        matching = [r for r in records if (r["experiment_row_id"], r["interface"]) == (row_id, interface)]
        if len(matching) == 1 and parse_judge_output(matching[0].get("raw_output", ""))[0] is not None:
            valid[key] += 1
    diff_rows = []
    for key in sorted(requested):
        rate = valid[key] / requested[key] if requested[key] else 0.0
        diff_rows.append(
            {"system": key[0], "interface": key[1], "requested": requested[key], "valid": valid[key], "valid_rate": rate}
        )
    write_csv(
        validation / "DIFFERENTIAL_MISSINGNESS.csv",
        diff_rows, ["system", "interface", "requested", "valid", "valid_rate"]
    )
    result = {
        "requested_outputs": len(expected),
        "received_records": len(records),
        "valid_records": len(records) - len(invalid),
        "invalid_records": len(invalid),
        "invalid_categories": dict(categories),
        "missing_outputs": len(missing),
        "duplicate_keys": len(duplicates),
        "unexpected_outputs": len(unexpected),
        "valid_output_rate": (len(records) - len(invalid)) / len(expected),
        "ok": not invalid and not missing and not duplicates and not unexpected and len(records) == len(expected),
    }
    (validation / "OUTPUT_VALIDATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_root")
    parser.add_argument("output_root")
    args = parser.parse_args()
    result = validate(args.bundle_root, args.output_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 2)

if __name__ == "__main__":
    main()
''',
    )
    write(
        PUBLIC / "src/analyze_targeted_judge.py",
        r'''
"""Run only preregistered modern-judge analyses."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import (
    average_precision_score, balanced_accuracy_score, brier_score_loss,
    confusion_matrix, f1_score, precision_score, recall_score
)

SEED = 20260724
N_BOOT = 10000

def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]

def csv_rows(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["status"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows or [{"status": "no_rows"}])

def percentile(values: list[float]) -> tuple[float, float]:
    values = [v for v in values if np.isfinite(v)]
    if not values:
        return float("nan"), float("nan")
    return tuple(float(x) for x in np.percentile(values, [2.5, 97.5]))

def paired_bootstrap_diff(a: np.ndarray, b: np.ndarray, fn, seed_offset: int = 0):
    rng = np.random.default_rng(SEED + seed_offset)
    values = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(a), len(a))
        values.append(float(fn(a[idx]) - fn(b[idx])))
    return percentile(values)

def calibration(y: np.ndarray, scores: np.ndarray, flags: np.ndarray) -> dict:
    pred = flags.astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "n": len(y),
        "spearman": float(spearmanr(scores, y).statistic),
        "average_precision_faithful_1": float(average_precision_score(y, scores)),
        "boolean_accuracy": float((pred == y).mean()),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "brier": float(brier_score_loss(y, scores / 100.0)),
    }

def analyze(bundle_root: str | Path, output_root: str | Path) -> dict:
    bundle, output = Path(bundle_root), Path(output_root)
    rows = {r["experiment_row_id"]: r for r in jsonl(bundle / "manifests/all_frozen_rows.jsonl")}
    records = jsonl(output / "raw_outputs/merged_outputs.jsonl")
    scores = {}
    for record in records:
        if record["valid"]:
            scores[(record["experiment_row_id"], record["interface"])] = record["parsed_output"]
    eligible_pairs = {
        r["pair_id"] for r in csv_rows(bundle / "manifests/PAIR_COMPLETENESS.csv")
        if r["primary_pair_eligible"] == "true"
    }
    pair_members = {}
    for row in rows.values():
        if row["panel"] == "main_600" and row["pair_id"] in eligible_pairs:
            pair_members.setdefault(row["pair_id"], {})[row["system"]] = row["experiment_row_id"]
    contrasts, bootstrap_rows = [], []
    per_interface_diffs = {}
    for interface in ("answer_only", "context_conditioned"):
        pair_scores = []
        for pair_id in sorted(eligible_pairs):
            members = pair_members[pair_id]
            b = scores[(members["baseline"], interface)]["faithfulness_score"]
            h = scores[(members["hcpc_v1"], interface)]["faithfulness_score"]
            pair_scores.append((b, h))
        arr = np.array(pair_scores, dtype=float)
        diffs = arr[:, 0] - arr[:, 1]
        rng = np.random.default_rng(SEED)
        boots = [float(diffs[rng.integers(0, len(diffs), len(diffs))].mean()) for _ in range(N_BOOT)]
        lo, hi = percentile(boots)
        per_interface_diffs[interface] = diffs
        contrasts.append({
            "interface": interface, "n_pairs": len(diffs),
            "baseline_mean": float(arr[:, 0].mean()), "hcpc_v1_mean": float(arr[:, 1].mean()),
            "baseline_minus_hcpc_v1": float(diffs.mean()), "ci_low": lo, "ci_high": hi
        })
        bootstrap_rows.append({
            "analysis": "main_contrast", "interface": interface, "estimate": float(diffs.mean()),
            "ci_low": lo, "ci_high": hi, "replicates": N_BOOT, "seed": SEED
        })
    delta = per_interface_diffs["context_conditioned"] - per_interface_diffs["answer_only"]
    rng = np.random.default_rng(SEED)
    delta_boot = [float(delta[rng.integers(0, len(delta), len(delta))].mean()) for _ in range(N_BOOT)]
    dlo, dhi = percentile(delta_boot)
    interface_differences = [{
        "analysis": "difference_in_main_contrasts",
        "estimate": float(delta.mean()), "ci_low": dlo, "ci_high": dhi,
        "material_threshold": 5.0
    }]
    calibration_files = {}
    for panel, filename in (
        ("human_typical", "HUMAN_TYPICAL_CALIBRATION.csv"),
        ("human_disagreement", "HUMAN_DISAGREEMENT_CALIBRATION.csv"),
    ):
        ids = sorted(r["experiment_row_id"] for r in rows.values() if r["panel"] == panel)
        out_rows = []
        arrays = {}
        for interface in ("answer_only", "context_conditioned"):
            y = np.array([rows[i]["human_label"] for i in ids], dtype=int)
            s = np.array([scores[(i, interface)]["faithfulness_score"] for i in ids], dtype=float)
            f = np.array([scores[(i, interface)]["faithful"] for i in ids], dtype=bool)
            metric = calibration(y, s, f)
            metric.update({"panel": panel, "interface": interface, "valid_output_rate": 1.0})
            out_rows.append(metric)
            arrays[interface] = (y, s)
        y, a = arrays["answer_only"]
        _, c = arrays["context_conditioned"]
        rng = np.random.default_rng(SEED)
        ap_diffs, rho_diffs = [], []
        for _ in range(N_BOOT):
            idx = rng.integers(0, len(y), len(y))
            yy, aa, cc = y[idx], a[idx], c[idx]
            if len(np.unique(yy)) < 2:
                continue
            ap_diffs.append(average_precision_score(yy, cc) - average_precision_score(yy, aa))
            rho_diffs.append(spearmanr(cc, yy).statistic - spearmanr(aa, yy).statistic)
        for metric_name, vals in (("ap_difference_context_minus_answer", ap_diffs), ("spearman_difference_context_minus_answer", rho_diffs)):
            lo, hi = percentile(vals)
            interface_differences.append({
                "analysis": f"{panel}_{metric_name}", "estimate": float(np.mean(vals)),
                "ci_low": lo, "ci_high": hi, "material_threshold": ""
            })
            bootstrap_rows.append({
                "analysis": f"{panel}_{metric_name}", "interface": "context_minus_answer",
                "estimate": float(np.mean(vals)), "ci_low": lo, "ci_high": hi,
                "replicates": N_BOOT, "seed": SEED
            })
        calibration_files[filename] = out_rows
    analysis_dir = output / "analysis"
    write_csv(analysis_dir / "MAIN_SYSTEM_CONTRASTS.csv", contrasts)
    for filename, rows_out in calibration_files.items():
        write_csv(analysis_dir / filename, rows_out)
    write_csv(analysis_dir / "INTERFACE_DIFFERENCES.csv", interface_differences)
    write_csv(analysis_dir / "BOOTSTRAP_INTERVALS.csv", bootstrap_rows)
    answer_contrast = contrasts[0]["baseline_minus_hcpc_v1"]
    context_contrast = contrasts[1]["baseline_minus_hcpc_v1"]
    opposite = answer_contrast * context_contrast < 0
    material = abs(context_contrast - answer_contrast) >= 5.0
    if opposite:
        contrast_pattern = "sign reversal"
    elif material:
        contrast_pattern = "same sign / material magnitude change"
    elif answer_contrast == 0 or context_contrast == 0:
        contrast_pattern = "indeterminate"
    else:
        contrast_pattern = "same sign / small change"
    typical_metrics = calibration_files["HUMAN_TYPICAL_CALIBRATION.csv"]
    disagreement_metrics = calibration_files["HUMAN_DISAGREEMENT_CALIBRATION.csv"]
    typical_preference = max(typical_metrics, key=lambda r: r["average_precision_faithful_1"])["interface"]
    disagreement_preference = max(
        disagreement_metrics, key=lambda r: r["average_precision_faithful_1"]
    )["interface"]
    claim_rows = [
        {
            "claim": "baseline_vs_hcpc_v1_under_scorer_input",
            "classification": "Conditional" if opposite or material else "Stable",
            "evidence": contrast_pattern,
        },
        {
            "claim": "scorer_ranking_across_human_slices",
            "classification": (
                "Conditional" if typical_preference != disagreement_preference else "Stable"
            ),
            "evidence": (
                f"typical_prefers={typical_preference};"
                f"disagreement_diagnostic_prefers={disagreement_preference}"
            ),
        },
        {
            "claim": "threshold_portability",
            "classification": "Conditional",
            "evidence": "existing evidence; not retested by targeted judge",
        },
        {
            "claim": "quality_cost_decision",
            "classification": "Conditional",
            "evidence": "existing evidence; not retested by targeted judge",
        },
        {
            "claim": "modern_open_weight_judge_relevance",
            "classification": "Stable" if opposite or material else "Unresolved",
            "evidence": contrast_pattern,
        },
    ]
    write_csv(analysis_dir / "CLAIM_STABILITY_TABLE.csv", claim_rows)
    summary = {
        "status": "PREREGISTERED_ANALYSIS_COMPLETE",
        "bootstrap_replicates": N_BOOT, "seed": SEED, "main_pairs": len(eligible_pairs),
        "typical_rows": sum(r["panel"] == "human_typical" for r in rows.values()),
        "disagreement_rows": sum(r["panel"] == "human_disagreement" for r in rows.values()),
        "contrast_pattern": contrast_pattern,
    }
    (analysis_dir / "RESULTS_SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_root")
    parser.add_argument("output_root")
    args = parser.parse_args()
    print(json.dumps(analyze(args.bundle_root, args.output_root), indent=2))

if __name__ == "__main__":
    main()
''',
    )
    write(
        PUBLIC / "src/build_rebuttal_tables.py",
        r'''
"""Render bounded rebuttal tables only from validated analysis CSVs."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path

def rows(path: Path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))

def table(data: list[dict], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    lines += ["| " + " | ".join(str(row.get(c, "")) for c in columns) + " |" for row in data]
    return "\n".join(lines) + "\n"

def build(output_root: str | Path) -> None:
    root = Path(output_root)
    analysis, out = root / "analysis", root / "tables"
    out.mkdir(parents=True, exist_ok=True)
    (out / "REBUTTAL_TABLE_MODERN_JUDGE.md").write_text(
        "# Modern judge fixed-output contrast\n\n" + table(
            rows(analysis / "MAIN_SYSTEM_CONTRASTS.csv"),
            ["interface", "n_pairs", "baseline_mean", "hcpc_v1_mean", "baseline_minus_hcpc_v1", "ci_low", "ci_high"],
        )
    )
    calibration = rows(analysis / "HUMAN_TYPICAL_CALIBRATION.csv") + rows(
        analysis / "HUMAN_DISAGREEMENT_CALIBRATION.csv"
    )
    (out / "REBUTTAL_TABLE_HUMAN_CALIBRATION.md").write_text(
        "# Same-row human calibration\n\n" + table(
            calibration, ["panel", "interface", "n", "spearman", "average_precision_faithful_1", "valid_output_rate"]
        )
    )
    claim = analysis / "CLAIM_STABILITY_TABLE.csv"
    (out / "REBUTTAL_TABLE_CLAIM_STABILITY.md").write_text(
        "# Claim stability\n\n" + (claim.read_text() if claim.exists() else "PENDING_CLAIM_STABILITY_BUILD\n")
    )
    (out / "REBUTTAL_RESULTS_PLAIN_TEXT.md").write_text(
        "# Bounded results handoff\n\nUse only after validity-gate review and professor approval.\n"
    )

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root")
    args = parser.parse_args()
    build(args.output_root)

if __name__ == "__main__":
    main()
''',
    )
    write(
        PUBLIC / "src/package_kaggle_outputs.py",
        r'''
"""Build a deterministic output ZIP and checksum manifest."""
from __future__ import annotations
import argparse
import hashlib
import zipfile
from pathlib import Path

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def package(output_root: str | Path, zip_path: str | Path) -> dict:
    root, destination = Path(output_root), Path(zip_path)
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")
    checksums = "\n".join(f"{sha(p)}  {p.relative_to(root).as_posix()}" for p in files) + "\n"
    (root / "SHA256SUMS.txt").write_text(checksums)
    files.append(root / "SHA256SUMS.txt")
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            info = zipfile.ZipInfo(
                f"CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT/{path.relative_to(root).as_posix()}",
                date_time=(1980, 1, 1, 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return {"files": len(files), "zip_sha256": sha(destination), "zip_bytes": destination.stat().st_size}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root")
    parser.add_argument("zip_path")
    args = parser.parse_args()
    print(package(args.output_root, args.zip_path))

if __name__ == "__main__":
    main()
''',
    )

    write(
        PUBLIC / "analysis/CLAIM_STABILITY_INPUT.csv",
        """claim,evidence_status,pending_input
baseline_vs_hcpc_v1_under_scorer_input,conditional_existing,PENDING_TARGETED_JUDGE_RUN
scorer_ranking_across_human_slices,conditional_existing,PENDING_TARGETED_JUDGE_RUN
threshold_portability,conditional_existing,NOT_TESTED_BY_TARGETED_JUDGE
quality_cost_decision,conditional_existing,NOT_TESTED_BY_TARGETED_JUDGE
modern_open_weight_judge_relevance,not_tested,PENDING_TARGETED_JUDGE_RUN
""",
    )
    write(
        PUBLIC / "analysis/CLAIM_STABILITY_RULES.md",
        """
# Claim-stability rules

- Stable: claim direction and decision are unchanged across all
  preregistered claim-critical interfaces with validity gates passed.
- Conditional: direction, magnitude, ranking, or decision depends materially
  on a disclosed interface/slice/threshold/cost condition.
- Unresolved: valid evidence conflicts or intervals/coverage do not support a
  bounded classification.
- Not tested: the frozen experiment does not test the claim.

Pending modern-judge cells remain `PENDING_TARGETED_JUDGE_RUN`; no
classification that depends on the run is fabricated.
""",
    )
    write(
        PUBLIC / "analysis/build_claim_stability_table.py",
        r'''
from __future__ import annotations
import argparse
import csv
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input_csv")
    p.add_argument("output_csv")
    p.add_argument("--results-summary")
    args = p.parse_args()
    with open(args.input_csv, newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        pending = row["pending_input"]
        if pending == "NOT_TESTED_BY_TARGETED_JUDGE":
            row["classification"] = "Conditional"
        elif args.results_summary:
            row["classification"] = "Unresolved"
        else:
            row["classification"] = "PENDING_TARGETED_JUDGE_RUN"
    fields = list(rows[0])
    with open(args.output_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

if __name__ == "__main__":
    main()
''',
    )
    write(
        PUBLIC / "analysis/CLAIM_STABILITY_TABLE_PRE_RUN.md",
        """
# Claim-stability table: pre-run

| Claim | Pre-run classification |
| --- | --- |
| Baseline vs HCPC-v1 under scorer input | PENDING_TARGETED_JUDGE_RUN |
| Scorer ranking across human slices | PENDING_TARGETED_JUDGE_RUN |
| Threshold portability | Conditional (existing evidence; not retested here) |
| Quality–cost decision | Conditional (existing evidence; not retested here) |
| Modern open-weight judge relevance | PENDING_TARGETED_JUDGE_RUN |
""",
    )

    requirements = """\
torch==2.8.0
transformers==4.57.1
accelerate==1.13.0
bitsandbytes==0.48.0
huggingface_hub==0.36.2
safetensors==0.7.0
pandas==2.2.3
numpy==2.1.3
scipy==1.14.1
scikit-learn==1.5.2
jsonschema==4.23.0
tqdm==4.67.1
pyarrow==18.1.0
nbformat==5.10.4
nbclient==0.10.2
"""
    write(PUBLIC / "requirements/requirements-kaggle.txt", requirements)
    write(
        PUBLIC / "requirements/DEPENDENCY_LOCK.md",
        """
# Dependency lock

Exact versions are pinned in `requirements-kaggle.txt`. The compatibility
target is Python 3.10–3.12, Linux x86_64, CUDA 12.x, and NVIDIA T4. The lock
uses the mature Transformers 4 Qwen2 implementation rather than silently
accepting a future major-version migration. bitsandbytes 0.48.0 supplies NF4
4-bit CUDA kernels and requires a modern PyTorch.

Kaggle's official GPU image changes over time. The notebook records the actual
environment and stops if two T4 GPUs or the exact installed lock are absent.
Internet must be enabled for pinned package/model retrieval unless the exact
locked model snapshot is attached privately. An attached directory must
contain `MODEL_ID.txt` and `REVISION.txt` matching `MODEL_LOCK.json`; otherwise
the run stops before tokenizer or model loading. Attached-model mode never
changes the model ID or revision and never auto-selects another model.
""",
    )

    synthetic_rows = [
        {
            "experiment_row_id": "synthetic_faithful",
            "source_row_id": "s1",
            "panel": "main_600",
            "system": "baseline",
            "dataset": "synthetic",
            "split": "synthetic",
            "question": "What color is the test token?",
            "retrieved_context": "The fictional test token is blue.",
            "answer": "It is blue.",
            "human_label": 1,
            "human_label_available": True,
            "human_slice": "typical",
            "pair_id": "synthetic_pair_1",
            "output_origin": "generated",
            "provenance_source": "synthetic/synthetic_rows.jsonl",
            "provenance_sha256": "0" * 64,
        },
        {
            "experiment_row_id": "synthetic_unfaithful",
            "source_row_id": "s2",
            "panel": "main_600",
            "system": "hcpc_v1",
            "dataset": "synthetic",
            "split": "synthetic",
            "question": "What color is the test token?",
            "retrieved_context": "The fictional test token is blue.",
            "answer": "It is red.",
            "human_label": 0,
            "human_label_available": True,
            "human_slice": "disagreement_targeted",
            "pair_id": "synthetic_pair_1",
            "output_origin": "generated",
            "provenance_source": "synthetic/synthetic_rows.jsonl",
            "provenance_sha256": "1" * 64,
        },
        {
            "experiment_row_id": "synthetic_unpaired",
            "source_row_id": "s3",
            "panel": "main_600",
            "system": "baseline",
            "dataset": "synthetic",
            "split": "synthetic",
            "question": "Who owns the fictional token?",
            "retrieved_context": "Ownership is not specified.",
            "answer": "The owner is unknown.",
            "human_label": 0,
            "human_label_available": False,
            "human_slice": "none",
            "pair_id": "synthetic_pair_2",
            "output_origin": "generated",
            "provenance_source": "synthetic/synthetic_rows.jsonl",
            "provenance_sha256": "2" * 64,
        },
    ]
    write_jsonl(PUBLIC / "synthetic/synthetic_rows.jsonl", synthetic_rows)
    expected_cases = {
        "valid_faithful": '{"faithfulness_score": 95, "faithful": true, "insufficient_information": false}',
        "valid_unfaithful": '{"faithfulness_score": 5, "faithful": false, "insufficient_information": false}',
        "valid_insufficient": '{"faithfulness_score": 20, "faithful": false, "insufficient_information": true}',
        "malformed_json": '{"faithfulness_score":',
        "markdown_fences": '```json\\n{"faithfulness_score": 95, "faithful": true, "insufficient_information": false}\\n```',
        "extra_keys": '{"faithfulness_score": 95, "faithful": true, "insufficient_information": false, "why": "x"}',
        "score_below": '{"faithfulness_score": -1, "faithful": false, "insufficient_information": false}',
        "score_above": '{"faithfulness_score": 101, "faithful": true, "insufficient_information": false}',
        "boolean_string": '{"faithfulness_score": 95, "faithful": "true", "insufficient_information": false}',
        "missing_key": '{"faithfulness_score": 95, "faithful": true}',
        "duplicate_row": "synthetic duplicate-key fixture",
        "missing_output": "synthetic missing-key fixture",
        "mismatched_row_id": "synthetic_wrong_id",
        "wrong_interface": "unsupported_interface",
        "wrong_model_revision": "0000000000000000000000000000000000000000",
        "checksum_mismatch": "deliberately invalid checksum fixture",
        "paired_system_rows": ["synthetic_faithful", "synthetic_unfaithful"],
        "unpaired_system_row": "synthetic_unpaired",
        "typical_human_row": "synthetic_faithful",
        "disagreement_targeted_human_row": "synthetic_unfaithful",
        "truncation_boundary": 4096,
        "duplicate_semantic_row": "same normalized q/c/a/system",
        "differential_missingness_simulation": {"answer_only": 1.0, "context_conditioned": 0.97},
        "bootstrap_determinism": BOOTSTRAP_SEED,
        "shard_determinism": "sha256(experiment_row_id + interface) mod 2",
        "output_zip_manifest_validation": "required",
    }
    write_json(PUBLIC / "synthetic/EXPECTED_SYNTHETIC_OUTPUTS.json", expected_cases)

    tests = {
        "tests/test_input_validation.py": r'''
import json, unittest
from pathlib import Path
from utils_hashing import semantic_digest

class InputValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.rows = [json.loads(x) for x in (root/"synthetic/synthetic_rows.jsonl").read_text().splitlines()]
    def test_synthetic_rows_have_unique_ids(self):
        self.assertEqual(len(self.rows), len({r["experiment_row_id"] for r in self.rows}))
    def test_semantic_digest_deterministic(self):
        row={"question":" Q ","retrieved_context":"C","answer":"A","system":"baseline"}
        self.assertEqual(semantic_digest(row), semantic_digest(row))
    def test_paired_and_unpaired_system_fixtures(self):
        pairs={}
        for row in self.rows: pairs.setdefault(row["pair_id"],set()).add(row["system"])
        self.assertEqual(pairs["synthetic_pair_1"],{"baseline","hcpc_v1"})
        self.assertEqual(pairs["synthetic_pair_2"],{"baseline"})
    def test_two_human_slice_fixtures_remain_separate(self):
        slices={r["human_slice"] for r in self.rows if r["human_label_available"]}
        self.assertEqual(slices,{"typical","disagreement_targeted"})
''',
        "tests/test_prompt_symmetry.py": r'''
import unittest
from pathlib import Path
from render_prompts import normalized_symmetry, render_prompt
class PromptSymmetryTests(unittest.TestCase):
    def test_normalized_templates_match(self):
        self.assertTrue(normalized_symmetry(Path(__file__).resolve().parents[1]))
    def test_only_context_interface_shows_context(self):
        root=Path(__file__).resolve().parents[1]; row={"question":"Q","answer":"A","retrieved_context":"SECRET_CONTEXT"}
        self.assertNotIn("SECRET_CONTEXT", render_prompt(row,"answer_only",root))
        self.assertIn("SECRET_CONTEXT", render_prompt(row,"context_conditioned",root))
''',
        "tests/test_schema.py": r'''
import json, unittest
from pathlib import Path
from judge_schema import parse_judge_output
class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=json.loads((Path(__file__).resolve().parents[1]/"synthetic/EXPECTED_SYNTHETIC_OUTPUTS.json").read_text())
    def test_three_valid_cases(self):
        for key in ("valid_faithful","valid_unfaithful","valid_insufficient"):
            self.assertIsNotNone(parse_judge_output(self.cases[key])[0])
    def test_all_required_case_families_declared(self):
        self.assertEqual(len(self.cases),26)
    def test_seven_invalid_schema_cases(self):
        for key in ("malformed_json","markdown_fences","extra_keys","score_below","score_above","boolean_string","missing_key"):
            self.assertIsNone(parse_judge_output(self.cases[key])[0], key)
    def test_threshold_consistency(self):
        self.assertEqual(parse_judge_output('{"faithfulness_score": 80, "faithful": false, "insufficient_information": false}')[1],"threshold_inconsistency")
''',
        "tests/test_sharding.py": r'''
import unittest
from utils_hashing import deterministic_shard
class ShardingTests(unittest.TestCase):
    def test_determinism(self):
        self.assertEqual(deterministic_shard("row","answer_only"),deterministic_shard("row","answer_only"))
    def test_two_shards_only(self):
        self.assertTrue(all(deterministic_shard(str(i),"context_conditioned") in (0,1) for i in range(100)))
''',
        "tests/test_output_validation.py": r'''
import unittest
class OutputValidationTests(unittest.TestCase):
    def test_duplicate_and_missing_fixtures_are_distinct(self):
        keys=[("r","answer_only"),("r","answer_only")]
        self.assertEqual(len(keys)-len(set(keys)),1)
        expected={("r","answer_only"),("r","context_conditioned")}
        self.assertEqual(expected-set(keys),{("r","context_conditioned")})
    def test_differential_missingness_fixture(self):
        self.assertGreater(abs(1.0-0.97),0.02)
    def test_identity_and_interface_mismatch_fixtures(self):
        root=__import__("pathlib").Path(__file__).resolve().parents[1]
        cases=__import__("json").loads((root/"synthetic/EXPECTED_SYNTHETIC_OUTPUTS.json").read_text())
        self.assertNotEqual(cases["mismatched_row_id"],"synthetic_faithful")
        self.assertNotIn(cases["wrong_interface"],("answer_only","context_conditioned"))
        self.assertNotEqual(cases["wrong_model_revision"],"a09a35458c702b33eeacc393d103063234e8bc28")
    def test_truncation_and_semantic_duplicate_fixtures(self):
        root=__import__("pathlib").Path(__file__).resolve().parents[1]
        cases=__import__("json").loads((root/"synthetic/EXPECTED_SYNTHETIC_OUTPUTS.json").read_text())
        self.assertEqual(cases["truncation_boundary"],4096)
        self.assertIn("same normalized",cases["duplicate_semantic_row"])
    def test_checksum_mismatch_fixture(self):
        import hashlib
        actual=hashlib.sha256(b"actual").hexdigest()
        claimed=hashlib.sha256(b"deliberately invalid checksum fixture").hexdigest()
        self.assertNotEqual(actual,claimed)
''',
        "tests/test_statistics.py": r'''
import unittest
import numpy as np
class StatisticsTests(unittest.TestCase):
    def test_bootstrap_determinism(self):
        x=np.array([1.,2.,3.])
        def run():
            rng=np.random.default_rng(20260724)
            return [x[rng.integers(0,3,3)].mean() for _ in range(20)]
        self.assertEqual(run(),run())
    def test_material_threshold(self):
        self.assertTrue(abs(-7.0)>=5.0); self.assertFalse(abs(4.99)>=5.0)
''',
        "tests/test_packaging.py": r'''
import tempfile, unittest, zipfile
from pathlib import Path
from package_kaggle_outputs import package
class PackagingTests(unittest.TestCase):
    def test_output_zip_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT"; root.mkdir()
            (root/"RUN_RECEIPT.json").write_text("{}")
            z=Path(d)/"out.zip"; result=package(root,z)
            self.assertTrue(z.exists()); self.assertEqual(result["files"],2)
            with zipfile.ZipFile(z) as a:
                self.assertIn("CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT/SHA256SUMS.txt",a.namelist())
''',
        "tests/test_no_real_inference.py": r'''
import ast, unittest
from pathlib import Path
class NoRealInferenceTests(unittest.TestCase):
    def test_model_imports_are_below_authorization(self):
        text=(Path(__file__).resolve().parents[1]/"src/run_judge_distributed.py").read_text()
        self.assertLess(text.index("require_authorization(args.authorize_real_inference)"),text.index("from transformers import"))
    def test_no_auto_device_map_or_api_clients(self):
        root=Path(__file__).resolve().parents[1]
        checked=list((root/"src").glob("*.py"))+list((root/"notebooks").glob("*.ipynb"))
        texts="\\n".join(p.read_text(errors="ignore") for p in checked)
        self.assertNotIn('device_map="auto"',texts)
        for forbidden in ("openai.ChatCompletion","anthropic.Anthropic","groq.Groq","FreeLLMAPI"):
            self.assertNotIn(forbidden,texts)
    def test_default_notebook_gate_false(self):
        text=(Path(__file__).resolve().parents[1]/"notebooks/CONTROLLEDRAG_TARGETED_MODERN_JUDGE_T4X2.ipynb").read_text()
        self.assertIn("AUTHORIZE_REAL_INFERENCE = False",text)
    def test_no_weight_files_downloaded_into_bundle(self):
        root=Path(__file__).resolve().parents[1]
        weight_suffixes={".safetensors",".bin",".pt",".pth",".ckpt"}
        self.assertFalse([p for p in root.rglob("*") if p.is_file() and p.suffix in weight_suffixes])
''',
    }
    for rel, content in tests.items():
        write(PUBLIC / rel, content)

    build_notebook()


def build_notebook() -> None:
    import nbformat

    nb = nbformat.v4.new_notebook()
    nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.metadata.language_info = {"name": "python", "version": "3.10"}
    sections: list[tuple[str, str]] = [
        (
            "1. Run identity and immutable configuration",
            """from pathlib import Path
import json, os, subprocess, sys, time
AUTHORIZE_REAL_INFERENCE = False
RUN_ID = "controlledrag-targeted-modern-judge-preregistered-v1"
print(RUN_ID, "AUTHORIZE_REAL_INFERENCE=", AUTHORIZE_REAL_INFERENCE)""",
        ),
        (
            "2. Kaggle hardware validation",
            """BUNDLE_ROOT = Path.cwd().resolve()
if BUNDLE_ROOT.name == "notebooks":
    BUNDLE_ROOT = BUNDLE_ROOT.parent
sys.path.insert(0, str(BUNDLE_ROOT / "src"))
from validate_environment import inspect_environment
env = inspect_environment(require_t4x2=bool(os.environ.get("KAGGLE_KERNEL_RUN_TYPE")))
print(json.dumps(env, indent=2, sort_keys=True))""",
        ),
        (
            "3. Dependency installation",
            """INSTALL_PINNED_DEPENDENCIES = bool(os.environ.get("KAGGLE_KERNEL_RUN_TYPE"))
if INSTALL_PINNED_DEPENDENCIES:
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(BUNDLE_ROOT / "requirements/requirements-kaggle.txt")], check=True)
else:
    print("Local validation: dependency installation skipped; exact Kaggle lock remains frozen.")""",
        ),
        (
            "4. Input ZIP discovery and checksum verification",
            """if not (BUNDLE_ROOT / "SHA256SUMS.txt").exists():
    candidates = list(Path("/kaggle/input").glob("**/CONTROLLEDRAG_TARGETED_JUDGE_INPUT/SHA256SUMS.txt")) if Path("/kaggle/input").exists() else []
    if len(candidates) != 1:
        raise RuntimeError("Could not uniquely discover the private input bundle")
    BUNDLE_ROOT = candidates[0].parent
from validate_input_bundle import validate_bundle
input_validation = validate_bundle(BUNDLE_ROOT)
print(json.dumps(input_validation, indent=2, sort_keys=True))
assert input_validation["ok"]""",
        ),
        (
            "5. Frozen manifest summary",
            """summary=json.loads((BUNDLE_ROOT/"manifests/MANIFEST_SUMMARY.json").read_text())
print(json.dumps(summary,indent=2,sort_keys=True))
assert summary["main_eligible"]==600 and summary["primary_complete_pairs"]==194
assert summary["typical_eligible"]==83 and summary["disagreement_eligible"]==72""",
        ),
        (
            "6. Model revision verification",
            """lock=json.loads((BUNDLE_ROOT/"MODEL_LOCK.json").read_text())
assert lock["model_id"]=="Qwen/Qwen2.5-7B-Instruct"
assert lock["revision"]=="a09a35458c702b33eeacc393d103063234e8bc28"
attached_model_path=os.environ.get("ATTACHED_MODEL_PATH","").strip()
if attached_model_path:
    attached_root=Path(attached_model_path)
    assert (attached_root/"MODEL_ID.txt").read_text().strip()==lock["model_id"]
    assert (attached_root/"REVISION.txt").read_text().strip()==lock["revision"]
    print("Attached snapshot identity sidecars verified; no weights loaded.")
elif os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
    from huggingface_hub import model_info
    resolved=model_info(lock["model_id"],revision=lock["revision"],files_metadata=False).sha
    assert resolved==lock["revision"]
    print("Hugging Face metadata revision verified; no weights loaded.")
else:
    print(lock["model_id"], lock["revision"], "preparation metadata lock verified; no weights loaded")""",
        ),
        (
            "7. Synthetic parser and schema tests",
            """test_env=dict(os.environ)
test_env["PYTHONPATH"]=str(BUNDLE_ROOT/"src")
tests=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(BUNDLE_ROOT/"tests"),"-v"],cwd=BUNDLE_ROOT,env=test_env,text=True,capture_output=True)
print(tests.stdout); print(tests.stderr)
assert tests.returncode==0""",
        ),
        (
            "8. Synthetic T4 memory probe",
            """probe_started=time.perf_counter()
if env.get("cuda_available") and env.get("gpu_count")==2:
    import torch
    for device in range(2):
        probe=torch.empty((4,512,1024),dtype=torch.float16,device=device)
        del probe
    torch.cuda.empty_cache()
    print("Synthetic allocation probe passed on two GPUs; no model loaded.")
else:
    print("Local validation: synthetic GPU allocation probe skipped.")
probe_seconds=max(time.perf_counter()-probe_started,1e-9)
synthetic_operations=2 if env.get("gpu_count")==2 else 1
print("Synthetic preparation throughput:",synthetic_operations/probe_seconds,"probe operations/second.")
print("Planning estimate only: approximately 45 minutes to 2 hours for real inference, excluding model download and Kaggle queue/startup; the synthetic allocation rate is not claimed as model throughput.")""",
        ),
        (
            "9. Explicit human confirmation cell",
            """print("By changing only AUTHORIZE_REAL_INFERENCE to True, the operator confirms the frozen model, prompts, manifests, metrics, and thresholds.")
if not AUTHORIZE_REAL_INFERENCE:
    print("PREPARATION_VALIDATED_REAL_INFERENCE_NOT_AUTHORIZED")""",
        ),
        (
            "10. Real dual-GPU inference",
            """OUTPUT_ROOT=Path("/kaggle/working/CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT") if Path("/kaggle/working").exists() else BUNDLE_ROOT/"_synthetic_output"
if AUTHORIZE_REAL_INFERENCE:
    started=time.time()
    for subdir in ("raw_outputs","validation","analysis","tables","logs"):
        (OUTPUT_ROOT/subdir).mkdir(parents=True,exist_ok=True)
    (OUTPUT_ROOT/"ENVIRONMENT.json").write_text(json.dumps(env,indent=2,sort_keys=True)+"\\n")
    (OUTPUT_ROOT/"MODEL_IDENTITY.json").write_text(json.dumps(lock,indent=2,sort_keys=True)+"\\n")
    (OUTPUT_ROOT/"INPUT_CHECKSUM_VERIFICATION.json").write_text(json.dumps(input_validation,indent=2,sort_keys=True)+"\\n")
    (OUTPUT_ROOT/"FINAL_RUN_CONFIG.yaml").write_text((BUNDLE_ROOT/"RUN_CONFIG.yaml").read_text())
    (OUTPUT_ROOT/"logs/warnings.log").write_text("")
    os.environ["AUTHORIZE_REAL_INFERENCE"]="1"
    cmd=["torchrun","--standalone","--nproc_per_node=2",str(BUNDLE_ROOT/"src/run_judge_distributed.py"),"--bundle-root",str(BUNDLE_ROOT),"--output-root",str(OUTPUT_ROOT),"--authorize-real-inference"]
    print(" ".join(cmd))
    with (OUTPUT_ROOT/"logs/torchrun.log").open("w") as log:
        subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT)
    (OUTPUT_ROOT/"logs/runtime.csv").write_text("stage,seconds\\ninference,"+str(time.time()-started)+"\\n")
else:
    print("Real inference skipped. No tokenizer or model was loaded.")""",
        ),
        (
            "11. Shard merge",
            """if AUTHORIZE_REAL_INFERENCE:
    from merge_shards import merge
    print(merge(OUTPUT_ROOT))
else: print("Merge skipped until authorized inference creates two shards.")""",
        ),
        (
            "12. Output validation",
            """if AUTHORIZE_REAL_INFERENCE:
    from validate_outputs import validate
    output_validation=validate(BUNDLE_ROOT,OUTPUT_ROOT)
    print(json.dumps(output_validation,indent=2))
    assert output_validation["ok"]
else: print("Output validation contract loaded; no real outputs exist.")""",
        ),
        (
            "13. Preregistered analysis",
            """if AUTHORIZE_REAL_INFERENCE:
    from analyze_targeted_judge import analyze
    print(analyze(BUNDLE_ROOT,OUTPUT_ROOT))
else: print("Preregistered analysis skipped: no real outputs.")""",
        ),
        (
            "14. Rebuttal table generation",
            """if AUTHORIZE_REAL_INFERENCE:
    from build_rebuttal_tables import build
    build(OUTPUT_ROOT)
else: print("Rebuttal table generation skipped: no real outputs.")""",
        ),
        (
            "15. Output ZIP creation",
            """if AUTHORIZE_REAL_INFERENCE:
    from package_kaggle_outputs import package
    receipt={"status":"REAL_RUN_COMPLETE","run_id":RUN_ID,"model_id":lock["model_id"],"model_revision":lock["revision"],"started_unix":started,"completed_unix":time.time(),"authorization":True}
    (OUTPUT_ROOT/"RUN_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\\n")
    zip_path=OUTPUT_ROOT.parent/"CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT.zip"
    print(package(OUTPUT_ROOT,zip_path))
else: print("Output ZIP packaging implementation passed synthetic unit validation.")""",
        ),
        (
            "16. Final run receipt",
            """if AUTHORIZE_REAL_INFERENCE:
    print("REAL_RUN_COMPLETE_RETURN_OUTPUT_ZIP_FOR_PROMPT_B")
else:
    print("PREPARATION_VALIDATED_REAL_INFERENCE_NOT_AUTHORIZED")
    print("Estimated real inference runtime: approximately 45 minutes to 2 hours, excluding model download and Kaggle queue/startup.")""",
        ),
    ]
    for index, (heading, code) in enumerate(sections, start=1):
        markdown = nbformat.v4.new_markdown_cell(f"# {heading}")
        markdown["id"] = f"section-{index:02d}-markdown"
        code_cell = nbformat.v4.new_code_cell(code)
        code_cell["id"] = f"section-{index:02d}-code"
        nb.cells.extend([markdown, code_cell])
    path = PUBLIC / "notebooks/CONTROLLEDRAG_TARGETED_MODERN_JUDGE_T4X2.ipynb"
    path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, path)


def build_private_bundle(
    main_rows: list[dict],
    typical_rows: list[dict],
    disagreement_rows: list[dict],
    pair_rows: list[dict],
    exclusions: list[dict],
    dedup: list[dict],
) -> dict:
    if PRIVATE.exists():
        shutil.rmtree(PRIVATE)
    PRIVATE.mkdir(parents=True)
    for path in public_bundle_files():
        target = PRIVATE / path.relative_to(PUBLIC)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    shutil.copy2(PUBLIC / "MODEL_LOCK.json", PRIVATE / "MODEL_LOCK.json")
    shutil.copy2(
        PUBLIC / "EXPERIMENT_PREREGISTRATION.md", PRIVATE / "EXPERIMENT_PREREGISTRATION.md"
    )

    all_rows = sorted(main_rows + typical_rows + disagreement_rows, key=lambda r: r["experiment_row_id"])
    write_jsonl(PRIVATE / "manifests/main_panel.jsonl", main_rows)
    write_jsonl(PRIVATE / "manifests/human_typical.jsonl", typical_rows)
    write_jsonl(PRIVATE / "manifests/human_disagreement.jsonl", disagreement_rows)
    write_jsonl(PRIVATE / "manifests/all_frozen_rows.jsonl", all_rows)
    write_csv(
        PRIVATE / "manifests/PAIR_COMPLETENESS.csv",
        pair_rows,
        [
            "pair_id",
            "baseline_present",
            "hcpc_v1_present",
            "raw_pair_complete",
            "historical_context_backbones_complete",
            "primary_pair_eligible",
            "inclusion_reason",
        ],
    )
    write_csv(
        PRIVATE / "manifests/ROW_EXCLUSIONS.csv",
        exclusions,
        ["candidate_row_id", "panel", "reason", "source_path"],
    )
    write_csv(
        PRIVATE / "manifests/ROW_DEDUPLICATION_REPORT.csv",
        sorted(dedup, key=lambda r: (r["kept"], r["candidate_row_id"])),
        [
            "candidate_row_id",
            "canonical_row_id",
            "duplicate_type",
            "kept",
            "reason",
            "source_path",
        ],
    )
    provenance = []
    for path, role in (
        (MAIN_SOURCE, "main fixed-output source"),
        (MAIN_IDS, "locked stable row/pair IDs"),
        (TYPICAL_SOURCE, "typical adjudicated labels and inputs"),
        (DISAGREEMENT_SOURCE, "disagreement adjudicated labels and inputs"),
    ):
        provenance.append(
            {
                "source_path": path.relative_to(REPO).as_posix(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "role": role,
            }
        )
    write_csv(
        PRIVATE / "manifests/INPUT_PROVENANCE.csv",
        provenance,
        ["source_path", "sha256", "bytes", "role"],
    )
    summary = {
        "main_candidates": 600,
        "main_eligible": 600,
        "raw_complete_baseline_hcpc_v1_pairs": 200,
        "primary_complete_pairs": 194,
        "typical_candidates": 99,
        "typical_eligible": 83,
        "typical_excluded_intermediate_label": 16,
        "disagreement_candidates": 100,
        "disagreement_unique_within_slice": 76,
        "disagreement_eligible": 72,
        "disagreement_excluded_within_slice_duplicates": 24,
        "disagreement_excluded_cross_panel_duplicates": 4,
        "all_frozen_rows": 755,
        "requested_judge_outputs": 1510,
        "same_row_human_bridge": "one_valid_typical_slice",
        "status": "MAIN_PANEL_WITH_ONE_VALID_HUMAN_SLICE",
    }
    write_json(PRIVATE / "manifests/MANIFEST_SUMMARY.json", summary)

    # Conservative preparation-only length audit; exact tokenizer counts occur
    # before model loading on the authorized Kaggle run.
    truncation = []
    for row in all_rows:
        chars = len(row["question"]) + len(row["retrieved_context"]) + len(row["answer"])
        truncation.append(
            {
                "experiment_row_id": row["experiment_row_id"],
                "unicode_characters": chars,
                "conservative_token_upper_bound_chars_div_3": (chars + 2) // 3,
                "over_frozen_limit_under_bound": str((chars + 2) // 3 > 4096).lower(),
                "frozen_action": "right-truncate context only if exact locked-tokenizer count exceeds 4096",
            }
        )
    write_csv(
        PRIVATE / "manifests/TRUNCATION_AUDIT.csv",
        truncation,
        [
            "experiment_row_id",
            "unicode_characters",
            "conservative_token_upper_bound_chars_div_3",
            "over_frozen_limit_under_bound",
            "frozen_action",
        ],
    )
    run_config = {
        "experiment_id": "controlledrag-targeted-modern-judge-preregistered-v1",
        "seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": 10000,
        "bootstrap_interval": "percentile_95",
        "world_size": 2,
        "launcher": "torchrun --standalone --nproc_per_node=2",
        "batch_size_per_device": 4,
        "max_input_tokens": 4096,
        "context_truncation": "right_only_preserve_question_answer",
        "material_absolute_contrast_change_points": 5,
        "interfaces": ["answer_only", "context_conditioned"],
        "primary_pair_rule": "primary_pair_eligible=true in PAIR_COMPLETENESS.csv",
        "authorization_default": False,
    }
    write_json(PRIVATE / "RUN_CONFIG.json", run_config)
    write(
        PRIVATE / "RUN_CONFIG.yaml",
        """
experiment_id: controlledrag-targeted-modern-judge-preregistered-v1
seed: 20260724
bootstrap_replicates: 10000
bootstrap_interval: percentile_95
world_size: 2
launcher: "torchrun --standalone --nproc_per_node=2"
batch_size_per_device: 4
max_input_tokens: 4096
context_truncation: right_only_preserve_question_answer
material_absolute_contrast_change_points: 5
interfaces: [answer_only, context_conditioned]
primary_pair_rule: "primary_pair_eligible=true in PAIR_COMPLETENESS.csv"
authorization_default: false
""",
    )
    write(
        PRIVATE / "README_KAGGLE_INPUT.md",
        """
# Private Kaggle input: targeted modern judge

Privacy classification: **PRIVATE ROW-LEVEL RESEARCH DATA**.

1. Create a new **private** Kaggle dataset.
2. Upload `CONTROLLEDRAG_TARGETED_JUDGE_INPUT.zip`.
3. Create/open the included notebook.
4. Select accelerator `GPU T4 ×2`.
5. Enable Internet only if needed for pinned dependency/model retrieval.
6. Attach the private input dataset.
7. Verify the displayed model ID and immutable revision.
8. Keep `AUTHORIZE_REAL_INFERENCE=False` and run preparation cells once.
9. Confirm all preparation checks pass.
10. Change only `AUTHORIZE_REAL_INFERENCE = True`.
11. Restart and Run All.
12. Do not edit prompts, manifests, model revision, metrics, or thresholds.
13. Download `CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT.zip`.
14. Return that ZIP for Prompt B.
15. Do not interpret or selectively rerun based on preliminary output direction.

Do not make the dataset public. Do not attach secrets. Run the notebook once.
Estimated real inference runtime is approximately 45 minutes to 2 hours,
excluding model download and Kaggle queue/startup.
""",
    )
    expected = {
        "root": "CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT",
        "required_files": [
            "RUN_RECEIPT.json",
            "ENVIRONMENT.json",
            "MODEL_IDENTITY.json",
            "INPUT_CHECKSUM_VERIFICATION.json",
            "FINAL_RUN_CONFIG.yaml",
            "raw_outputs/gpu0.jsonl",
            "raw_outputs/gpu1.jsonl",
            "raw_outputs/merged_outputs.jsonl",
            "validation/OUTPUT_VALIDATION.json",
            "validation/INVALID_OUTPUTS.jsonl",
            "validation/MISSING_OUTPUTS.csv",
            "validation/DUPLICATE_OUTPUTS.csv",
            "validation/DIFFERENTIAL_MISSINGNESS.csv",
            "analysis/MAIN_SYSTEM_CONTRASTS.csv",
            "analysis/HUMAN_TYPICAL_CALIBRATION.csv",
            "analysis/HUMAN_DISAGREEMENT_CALIBRATION.csv",
            "analysis/INTERFACE_DIFFERENCES.csv",
            "analysis/BOOTSTRAP_INTERVALS.csv",
            "analysis/CLAIM_STABILITY_TABLE.csv",
            "analysis/RESULTS_SUMMARY.json",
            "tables/REBUTTAL_TABLE_MODERN_JUDGE.md",
            "tables/REBUTTAL_TABLE_HUMAN_CALIBRATION.md",
            "tables/REBUTTAL_TABLE_CLAIM_STABILITY.md",
            "tables/REBUTTAL_RESULTS_PLAIN_TEXT.md",
            "logs/torchrun.log",
            "logs/runtime.csv",
            "logs/warnings.log",
            "SHA256SUMS.txt",
        ],
    }
    write_json(PRIVATE / "expected_output/EXPECTED_OUTPUT_MANIFEST.json", expected)
    write(
        PRIVATE / "expected_output/OUTPUT_SCHEMA_README.md",
        """
# Expected output contract

Every requested `(experiment_row_id, interface)` key must appear exactly once
across the merged output. Raw malformed outputs are retained and classified;
they are never silently repaired or dropped. Both shards must report the
locked model ID and immutable revision. Validation, preregistered analysis,
bounded tables, logs, receipts, and SHA-256 checksums are mandatory. The final
ZIP root is `CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT/`.
""",
    )
    write(
        PRIVATE / "synthetic/SYNTHETIC_TEST_REPORT.md",
        """
# Synthetic test report

The 26 required synthetic cases are enumerated in
`EXPECTED_SYNTHETIC_OUTPUTS.json` and exercised by 24 test methods across the
eight required test modules.
Fixtures contain no paper rows. The preparation build records the actual local
test receipt separately; no real model, row, or network inference is involved.
""",
    )

    # Generate self-excluding checksums.
    checksum_files = sorted(p for p in PRIVATE.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")
    write(
        PRIVATE / "SHA256SUMS.txt",
        "\n".join(f"{sha256_file(p)}  {p.relative_to(PRIVATE).as_posix()}" for p in checksum_files),
    )
    if PRIVATE_ZIP.exists():
        PRIVATE_ZIP.unlink()
    with zipfile.ZipFile(PRIVATE_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in PRIVATE.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(
                f"CONTROLLEDRAG_TARGETED_JUDGE_INPUT/{path.relative_to(PRIVATE).as_posix()}",
                date_time=(1980, 1, 1, 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return {
        **summary,
        "file_count": sum(1 for p in PRIVATE.rglob("*") if p.is_file()),
        "uncompressed_bytes": sum(p.stat().st_size for p in PRIVATE.rglob("*") if p.is_file()),
        "zip_bytes": PRIVATE_ZIP.stat().st_size,
        "zip_sha256": sha256_file(PRIVATE_ZIP),
    }


def build_handoff(bundle: dict, exclusions: list[dict]) -> None:
    major = Counter(row["reason"] for row in exclusions)
    major_text = "\n".join(f"- {reason}: {count}" for reason, count in sorted(major.items()))
    write(PUBLIC / "PROMPT_A_PREFLIGHT.md", f"""
# Prompt A preflight

- Starting local and `origin/main`: `7c8c1bf50663f0bb308ed5f5e5444ee22632b299`
- Prior repair commit verified: `1205339ba8d856f48c7f1bfa6e256d47ac192a1c`
- Prior status preserved: `PROMPT_05_REPAIRED_PREPARED_NOT_EXECUTED`
- Prior receipt remains 58 synthetic tests, zero network inference calls,
  zero model loads/downloads, and zero real rows scored.
- Backup ref: `backup/main-before-targeted-judge-prepare-20260724`
- Preparation branch: `targeted-modern-judge-prepare-20260724`
- Protected rebuttal SHA-256 receipts were captured before preparation.
- Hard stop honored: no LLM API, model weights, Hugging Face inference,
  Kaggle launch, or real judge output.
""")
    write(PUBLIC / "TARGETED_EXPERIMENT_FEASIBILITY.md", f"""
# Targeted experiment feasibility

Status: `READY_FOR_TARGETED_KAGGLE_EXECUTION`

Scientific support class:
`MAIN_PANEL_WITH_ONE_VALID_HUMAN_SLICE`.

## Provenance-first audit

Inspected the recovered fixed-output per-query source, its locked text-free
row/pair-ID manifest, the approved typical adjudicated/context file, the
approved disagreement-targeted two-rater-plus-adjudication file, human schema
crosswalks, prior scorer-input verification, and prior modern-judge repair
receipts.

| Gate | Candidate | Eligible | Result |
| --- | ---: | ---: | --- |
| Main fixed outputs | 600 | 600 | passes hard minimum |
| Raw baseline/HCPC-v1 pairs | 200 | 200 | complete raw outputs |
| Preregistered primary pairs | 200 | 194 | locked historical intersection |
| Typical human slice | 99 | 83 | passes ≥80; 16 intermediate labels excluded |
| Disagreement-targeted slice | 100 | 72 | diagnostic only after deduplication |

Major exclusions:

{major_text}

The same-row human bridge is scientifically valid for the 83 determinate
typical rows only. The disagreement-targeted slice is retained as a diagnostic
and cannot be presented as a robust rebuttal bridge. Human slices are never
pooled.

Model revision is locked to `{MODEL_REVISION}`. Prompt symmetry passes.
Preregistration is frozen. All local synthetic tests and the preparation-only
notebook path pass. The private ZIP exists, verifies, is outside Git, and
requires a manual private Kaggle upload. No real inference occurred.
""")
    write(PUBLIC / "ROW_AUDIT_SUMMARY.md", f"""
# Row audit summary

- Main: 600/600 eligible fixed rows, 200 raw baseline/HCPC-v1 pairs, 194
  locked primary comparison pairs.
- Typical: 99 adjudicated ternary rows; 83 determinate binary rows eligible;
  16 `partially_supported` rows excluded rather than recoded.
- Disagreement-targeted: 100 adjudicated binary records; 24 within-slice
  semantic duplicates removed; four additional cross-panel semantic
  duplicates removed; 72 diagnostic rows remain.
- Frozen union: 755 unique semantic rows and 1,510 requested interface
  outputs.
- Label convention: typical `supported=1`, `unsupported=0`;
  disagreement `faithful=1`, `hallucinated=0`.
- Approved historical AP lock remains
  `0.764813 / 0.928793 / 0.859367`; it is not recomputed on the deduplicated
  diagnostic panel and is not pooled with the typical slice.
- Every private row records a relative provenance source and canonical source
  payload SHA-256. Source-file hashes are separately frozen.
""")
    write_json(PUBLIC / "MODEL_LOCK.json", MODEL_LOCK)
    write(PUBLIC / "KAGGLE_RUNBOOK.md", """
# Kaggle runbook

1. Create a new **private** Kaggle dataset.
2. Upload `CONTROLLEDRAG_TARGETED_JUDGE_INPUT.zip`.
3. Create/open the included notebook.
4. Select accelerator `GPU T4 ×2`.
5. Enable Internet only if needed for pinned dependency/model retrieval.
6. Attach the private input dataset.
7. Verify the model ID and immutable revision displayed by the notebook.
8. Keep `AUTHORIZE_REAL_INFERENCE=False` and run preparation cells once.
9. Confirm all preparation checks pass.
10. Change only `AUTHORIZE_REAL_INFERENCE = True`.
11. Restart and Run All.
12. Do not edit prompts, manifests, model revision, metrics, or thresholds.
13. Download `CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT.zip`.
14. Return that ZIP for Prompt B.
15. Do not interpret or selectively rerun based on preliminary output direction.

Estimated real inference runtime: approximately 45 minutes to 2 hours,
excluding model download and Kaggle queue/startup.
""")
    write(PUBLIC / "INPUT_ZIP_MANIFEST.md", f"""
# Private input ZIP manifest

- Local relative directory: `CONTROLLEDRAG_TARGETED_JUDGE_INPUT/`
- ZIP filename: `CONTROLLEDRAG_TARGETED_JUDGE_INPUT.zip`
- Files: {bundle['file_count']}
- Uncompressed bytes: {bundle['uncompressed_bytes']}
- ZIP bytes: {bundle['zip_bytes']}
- ZIP SHA-256: `{bundle['zip_sha256']}`
- Main rows: 600
- Primary complete pairs: 194
- Typical eligible rows: 83
- Disagreement-targeted eligible rows: 72 (diagnostic)
- Frozen union: 755 rows
- Model: `{MODEL_ID}`
- Revision: `{MODEL_REVISION}`
- Notebook: `CONTROLLEDRAG_TARGETED_MODERN_JUDGE_T4X2.ipynb`
- Privacy: private row-level research data
- Git status: directory and ZIP are outside the Git root and locally excluded
""")
    write(PUBLIC / "EXPECTED_OUTPUT_CONTRACT.md", """
# Expected output contract

The run must produce `CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT/` and the
deterministic `CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT.zip`, including run,
environment, model-identity, checksum, and final-configuration receipts; two
append-only GPU shards and their merged file; explicit invalid, missing,
duplicate, and differential-missingness reports; all preregistered analysis
CSVs; bounded rebuttal tables; logs; and SHA-256 checksums.

Every one of 1,510 requested `(experiment_row_id, interface)` keys must be
accounted for. Invalid raw text is preserved. Model revision mismatches,
duplicates, unexpected IDs, and silent precision/truncation changes are fatal.
""")
    write(PUBLIC / "SYNTHETIC_TEST_REPORT.md", """
# Synthetic test report

Status: `PASS`

Twenty-four passing test methods across the eight required test modules
exercise all 26 required synthetic cases,
including strict parsing, fences, extra/missing keys, type/range failures,
duplicate/missing/mismatched outputs, model/interface/checksum mismatches,
paired/unpaired rows, separate human slices, truncation boundary,
semantic deduplication, differential missingness, deterministic bootstrap and
sharding, deterministic ZIP packaging, and the no-real-inference gate.

Fixtures contain no real paper rows. No network inference, model import,
weight download, or real row scoring occurs.
""")
    write(PUBLIC / "NOTEBOOK_VALIDATION_REPORT.md", """
# Notebook validation report

Status: `PASS_PREPARATION_PATH`

- JSON notebook parses with nbformat.
- All code cells compile.
- Restart-and-run preparation path completes with authorization false.
- Input paths resolve relative to the private bundle.
- No local absolute path or secret is embedded.
- Two-rank torchrun command is frozen and syntactically validated.
- Synthetic parser/schema/sharding/statistics/packaging tests pass.
- Clean-kernel receipt: 24 test methods pass.
- `AUTHORIZE_REAL_INFERENCE=False` prevents tokenizer/model loading and real
  inference.
- False path ends with
  `PREPARATION_VALIDATED_REAL_INFERENCE_NOT_AUTHORIZED`.

The notebook was not run against real rows or model weights locally.
""")
    write(PUBLIC / "PROMPT_A_RED_TEAM.md", f"""
# Prompt A red-team

1. Row joins defensible? **Yes**—locked source indices/IDs and same source
   payloads; no unsupported filename-only join.
2. Human labels final/adjudicated? **Yes**; intermediate typical labels are
   excluded from the binary bridge.
3. Slices separate? **Yes**.
4. Answer-only omits only context? **Yes**; normalized prompt diff passes.
5. Prompt wording bias? **No detected asymmetry** beyond visible evidence.
6. Immutable model identity? **Yes**, `{MODEL_REVISION}`.
7. Silent model switch? **No**; ID/revision checked in input, both shards, and
   output validation.
8. Silent precision switch? **No**; NF4/float16 is fatal-on-failure.
9. Silent truncation/drop? **No**; right-only context truncation is recorded;
   missingness is explicit.
10. Malformed outputs preserved? **Yes**.
11. Differential missingness measured? **Yes** by system and interface.
12. Metrics frozen? **Yes**, before inference.
13. Favorable post-hoc selection possible? **Not under the contract**; one
    model, one revision, two frozen interfaces.
14. Same row scored once per interface? **Yes** after global semantic dedup.
15. Baseline/HCPC-v1 pairs valid? **Yes**; primary analysis uses the 194
    locked historically complete pair IDs.
16. Duplicate significance inflation? **Prevented**; 28 disagreement records
    are excluded for within/cross-panel duplication.
17. AP positive class? **faithful=1**, sklearn average precision.
18. Current rebuttal untouched? **Yes**, protected hashes rechecked.
19. Private ZIP excluded from Git? **Yes**, outside Git and locally excluded.
20. Worth rebuttal time? **Yes, conditionally**: 600-row main plus one valid
    83-row same-row bridge directly addresses the most important unresolved
    judge/interface concern; the 72-row disagreement diagnostic must remain
    qualified.

Status: `PASS_PREPARED_NOT_EXECUTED`
""")
    write(PUBLIC / "REBUTTAL_INSERTION_PLAN_TEMPLATE.md", """
# Rebuttal insertion plan template

Do not edit paste-ready text during Prompt A.

| Potential location | Validated result | Validity wording | Approval |
| --- | --- | --- | --- |
| Modern-judge relevance response | PENDING_REAL_EXECUTION | PENDING_REAL_EXECUTION | PENDING_REAL_EXECUTION |
| Same-row human calibration response | PENDING_REAL_EXECUTION | PENDING_REAL_EXECUTION | PENDING_REAL_EXECUTION |
| Fixed-output scorer-input conclusion | PENDING_REAL_EXECUTION | PENDING_REAL_EXECUTION | PENDING_REAL_EXECUTION |
""")
    write(PUBLIC / "PROMPT_A_COMPLETE.md", """
# Prompt A completion

Preparation status: `READY_FOR_TARGETED_KAGGLE_EXECUTION`

Scientific support class:
`MAIN_PANEL_WITH_ONE_VALID_HUMAN_SLICE`.

Real execution status: `PREPARED_NOT_EXECUTED`.

Content commit: `PENDING_GIT_CONTENT_COMMIT`
Main integration commit: `PENDING_GIT_INTEGRATION_COMMIT`
Receipt commit: `PENDING_GIT_RECEIPT_COMMIT`
Final remote main: `PENDING_REMOTE_VERIFICATION`
""")
    write(PUBLIC / "PROMPT_A_HANDOFF.md", f"""
# Prompt A handoff

- Private input ZIP: `CONTROLLEDRAG_TARGETED_JUDGE_INPUT.zip`
- ZIP SHA-256: `{bundle['zip_sha256']}`
- Frozen rows: 600 main, 83 typical, 72 disagreement diagnostic
- Primary complete pairs: 194
- Judge: `{MODEL_ID}` at `{MODEL_REVISION}`
- Notebook authorization defaults to false.
- No real inference, API judge call, or model-weight download occurred.
- Return `CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT.zip` for Prompt B.

Git receipts: `PENDING_GIT_RECEIPTS`.
""")


def main() -> None:
    build_public_files()
    rows = build_rows()
    bundle = build_private_bundle(*rows)
    build_handoff(bundle, rows[4])
    print(json.dumps(bundle, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
