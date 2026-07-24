#!/usr/bin/env python3
"""Context-conditioned NLI rescoring for the fixed-generation rows.

The frozen artifact's DeBERTa and roberta-large-mnli faithfulness columns
are *legacy zero-shot label proxies*: the answer sentence is the
sequence classified against {entailment, neutral, contradiction} with
``hypothesis_template="{}"`` and the retrieved context is NOT consumed.

This script implements the proper NLI calling convention:
    premise    = retrieved context (truncated to model max-length)
    hypothesis = generated answer (or single answer sentence)
    score      = softmax(logits)[entailment_label_index]

For multi-sentence answers the per-sentence entailment probabilities
are averaged. This is the same aggregation used by the legacy
``HallucinationDetector`` so the contrast against the legacy proxy is
apples-to-apples.

Usage examples (run from repo root):

    # Quick smoke test (50 rows, both models, MPS):
    python3 scripts/run_context_conditioned_nli_scoring.py \\
        --input data/revision/fix_03/per_query.csv \\
        --output results/revision/context_conditioned_nli/per_query_smoke.csv \\
        --max_rows 50 \\
        --models cross-encoder/nli-deberta-v3-base roberta-large-mnli

    # Larger subset (600 rows balanced across conditions):
    python3 scripts/run_context_conditioned_nli_scoring.py \\
        --input data/revision/fix_03/per_query.csv \\
        --output results/revision/context_conditioned_nli/per_query_n600.csv \\
        --balanced_per_condition 200 \\
        --models cross-encoder/nli-deberta-v3-base roberta-large-mnli

    # Full 7500 rows (slow on MPS, ~30-60 min per model):
    python3 scripts/run_context_conditioned_nli_scoring.py \\
        --input data/revision/fix_03/per_query.csv \\
        --output results/revision/context_conditioned_nli/per_query_full.csv \\
        --models cross-encoder/nli-deberta-v3-base roberta-large-mnli

The script is resumable: if --output already exists, completed rows are
skipped on re-run. No paid APIs are used.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import torch


# --------------------------------------------------------------------- #
# Sentence splitting (simple period-based, matching the legacy detector)
# --------------------------------------------------------------------- #
_SENT_PATTERN = re.compile(r"[.!?]\s+")


def split_sentences(answer: str, min_chars: int = 10) -> List[str]:
    if not isinstance(answer, str):
        return []
    parts = _SENT_PATTERN.split(answer.strip())
    parts = [p.strip(" .") for p in parts]
    return [p for p in parts if len(p) > min_chars]


def truncate_premise(text: str, max_chars: int = 2048) -> str:
    if not isinstance(text, str):
        return ""
    return text.strip()[:max_chars]


# --------------------------------------------------------------------- #
# Model wrappers
# --------------------------------------------------------------------- #
def pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


class NLIModel:
    """Thin context-conditioned NLI wrapper around AutoModelForSequenceClassification.

    Returns the entailment probability for each (premise, hypothesis) pair.
    Handles both DeBERTa-v3 NLI and roberta-large-mnli label orderings.
    """

    def __init__(self, model_name: str, device: torch.device, max_length: int = 512):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        print(f"[NLI] Loading {model_name} on {device}", flush=True)
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(device)
        self.model.eval()
        self.device = device
        self.max_length = max_length
        self.entailment_idx = self._resolve_entailment_index()
        print(
            f"[NLI] {model_name}: id2label={self.model.config.id2label}, "
            f"entailment_idx={self.entailment_idx}",
            flush=True,
        )

    def _resolve_entailment_index(self) -> int:
        id2label = self.model.config.id2label
        for idx, label in id2label.items():
            label_l = str(label).lower()
            if "entail" in label_l:
                return int(idx)
        # Fall back to last index, which is the convention for several MNLI models.
        return len(id2label) - 1

    @torch.no_grad()
    def score_pairs(self, pairs: Iterable[tuple], batch_size: int = 8) -> List[float]:
        scores: List[float] = []
        batch: List[tuple] = []
        for pair in pairs:
            batch.append(pair)
            if len(batch) >= batch_size:
                scores.extend(self._score_batch(batch))
                batch = []
        if batch:
            scores.extend(self._score_batch(batch))
        return scores

    def _score_batch(self, batch: List[tuple]) -> List[float]:
        premises = [p for p, _ in batch]
        hypotheses = [h for _, h in batch]
        enc = self.tokenizer(
            premises,
            hypotheses,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length,
        ).to(self.device)
        out = self.model(**enc)
        probs = torch.softmax(out.logits, dim=-1)
        return probs[:, self.entailment_idx].detach().cpu().tolist()


# --------------------------------------------------------------------- #
# Per-row scorer
# --------------------------------------------------------------------- #
def context_conditioned_score(model: NLIModel, context: str, answer: str) -> float:
    """Mean entailment probability over answer sentences vs the full context."""
    sents = split_sentences(answer)
    if not sents:
        return float("nan")
    premise = truncate_premise(context)
    pairs = [(premise, s) for s in sents]
    sentence_scores = model.score_pairs(pairs)
    if not sentence_scores:
        return float("nan")
    return float(sum(sentence_scores) / len(sentence_scores))


# --------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------- #
def select_subset(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    if args.max_rows and args.max_rows > 0:
        return df.head(args.max_rows).copy()
    if args.balanced_per_condition and args.balanced_per_condition > 0:
        per = args.balanced_per_condition
        parts = []
        for cond in sorted(df["condition"].unique()):
            sub = df[df["condition"] == cond].head(per)
            parts.append(sub)
        return pd.concat(parts, axis=0).reset_index(drop=True)
    return df.copy()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument(
        "--models",
        nargs="+",
        default=["cross-encoder/nli-deberta-v3-base", "roberta-large-mnli"],
    )
    p.add_argument("--max_rows", type=int, default=0)
    p.add_argument("--balanced_per_condition", type=int, default=0)
    p.add_argument("--batch_size", type=int, default=8)
    p.add_argument("--max_length", type=int, default=512)
    args = p.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(in_path)
    df = select_subset(df, args)
    print(f"[NLI] Input rows: {len(df)} (from {in_path})", flush=True)

    if "context" not in df.columns or "answer" not in df.columns:
        raise SystemExit(
            "Input CSV must contain 'context' and 'answer' columns; got "
            f"{list(df.columns)}"
        )

    device = pick_device()
    print(f"[NLI] Device: {device}", flush=True)

    short_names = {
        "cross-encoder/nli-deberta-v3-base": "deberta_ctx",
        "roberta-large-mnli": "roberta_mnli_ctx",
    }

    completed_path = out_path.with_suffix(out_path.suffix + ".partial")

    if out_path.exists():
        prev = pd.read_csv(out_path)
        # Resume: assume same row order; copy any already-computed columns onto df
        for col in prev.columns:
            if col not in df.columns:
                df[col] = prev[col].reindex(df.index).values
        print(f"[NLI] Resumed from {out_path} ({len(prev)} rows present)", flush=True)

    for mn in args.models:
        col = "faith_" + short_names.get(mn, re.sub(r"[^a-z0-9]+", "_", mn.lower()))
        if col in df.columns and df[col].notna().sum() == len(df):
            print(f"[NLI] Skipping {mn} (column {col} already complete)", flush=True)
            continue
        print(f"[NLI] Scoring with {mn} -> column {col}", flush=True)
        model = NLIModel(mn, device, max_length=args.max_length)
        scores: List[float] = []
        t0 = time.time()
        for i, row in enumerate(df.itertuples(index=False)):
            ctx = getattr(row, "context", "")
            ans = getattr(row, "answer", "")
            try:
                s = context_conditioned_score(model, ctx, ans)
            except Exception as e:  # noqa: BLE001
                print(f"[NLI] row {i} failed: {e}", flush=True)
                s = float("nan")
            scores.append(s)
            if (i + 1) % 50 == 0:
                rate = (i + 1) / max(1.0, time.time() - t0)
                remaining = (len(df) - (i + 1)) / max(1e-6, rate)
                print(
                    f"[NLI]   {i + 1}/{len(df)} done "
                    f"({rate:.2f} rows/s, eta {remaining/60:.1f} min)",
                    flush=True,
                )
                # Periodic checkpoint
                df_partial = df.copy()
                df_partial[col] = pd.Series(scores + [float("nan")] * (len(df) - len(scores)))
                df_partial.to_csv(completed_path, index=False)
        df[col] = scores
        df.to_csv(out_path, index=False)
        del model
        if device.type == "mps":
            torch.mps.empty_cache()
        elif device.type == "cuda":
            torch.cuda.empty_cache()

    df.to_csv(out_path, index=False)
    print(f"[NLI] Wrote {out_path}", flush=True)
    if completed_path.exists():
        try:
            completed_path.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    main()
