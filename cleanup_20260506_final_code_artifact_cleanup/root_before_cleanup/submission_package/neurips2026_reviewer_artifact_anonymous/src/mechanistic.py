"""
src/mechanistic.py
HuggingFace-based attention analysis for §7.5 "Mechanistic Evidence".

Loads a generator (default Mistral-7B-Instruct-v0.2) with output_attentions=True,
runs it over matched (coherent, fragmented) prompt pairs, and extracts:

  - attention_entropy: per layer × head × output-token, Shannon entropy of
    the attention distribution over the full input prompt
  - retrieved_mass: per layer × head × output-token, fraction of attention
    mass that falls on tokens belonging to retrieved-passage spans
  - parametric_mass: fraction of attention mass on BOS + instruction tokens
    (i.e., positions OUTSIDE the retrieved-passage spans)
  - per_output_token_attribution: for each generated token, the top-k source
    spans it attended to — enables qualitative "this hallucinated token
    came from parametric memory, not retrieved context" claims.

All heavy operations are lazy-loaded; the module is safe to import without
a GPU. Pass device="cuda"/"mps"/"cpu" at construction time.

Compute envelope (Mistral-7B fp16):
  - VRAM: ~14-16 GB (fits on a T4 if we disable kv-cache storage of attentions
    by processing short prompts; on a 3090/4090 comfortably)
  - Time: ~3-5 s per prompt with max_new_tokens=64 on a 3090
  - For 120 adversarial cases × 2 conditions: ~15-20 minutes on a 3090
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch


@dataclass
class AttentionAnalysis:
    """Container for one prompt's attention analysis."""
    prompt:                 str
    output_text:            str
    input_token_count:      int
    output_token_count:     int
    retrieved_token_ranges: List[Tuple[int, int]]  # (start, end) per passage
    parametric_token_ranges: List[Tuple[int, int]]  # BOS + instruction + query

    # Per-layer/head/output-token arrays, stored as numpy after detaching.
    # shape: (n_layers, n_heads, n_output_tokens)
    attention_entropy:      np.ndarray
    retrieved_mass:         np.ndarray
    parametric_mass:        np.ndarray

    # Top-k attribution per output token (for qualitative analysis)
    top_k_attribution:      List[List[Dict]] = field(default_factory=list)

    def aggregate(self) -> Dict[str, float]:
        """Summarize over (layers, heads, output tokens)."""
        return {
            "mean_entropy":       float(np.nanmean(self.attention_entropy)),
            "mean_retrieved_mass": float(np.nanmean(self.retrieved_mass)),
            "mean_parametric_mass": float(np.nanmean(self.parametric_mass)),
            "p25_retrieved_mass": float(np.nanpercentile(self.retrieved_mass, 25)),
            "p75_retrieved_mass": float(np.nanpercentile(self.retrieved_mass, 75)),
        }


class AttentionProbe:
    """
    Loads an instruction-tuned generator and produces AttentionAnalysis
    objects for arbitrary prompts where we know which token ranges came
    from retrieved passages.

    Usage
    -----
        probe = AttentionProbe(model_name="mistralai/Mistral-7B-Instruct-v0.2",
                               device="cuda")

        analysis = probe.analyze(
            system_instruction="Answer based only on context.",
            retrieved_passages=["passage 1 text...", "passage 2 text..."],
            query="What is X?",
            max_new_tokens=64,
        )

        summary = analysis.aggregate()
    """

    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
        device: Optional[str] = None,
        dtype: str = "float16",
    ):
        self.model_name = model_name
        self.device = device or self._auto_device()
        self.dtype  = getattr(torch, dtype)
        self._model = None
        self._tok   = None

    @staticmethod
    def _auto_device() -> str:
        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _lazy_load(self):
        if self._model is not None:
            return
        from transformers import AutoTokenizer, AutoModelForCausalLM
        print(f"[Probe] Loading tokenizer: {self.model_name}")
        self._tok = AutoTokenizer.from_pretrained(self.model_name)
        print(f"[Probe] Loading model: {self.model_name} (dtype={self.dtype}, device={self.device})")
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=self.dtype,
            attn_implementation="eager",   # required for output_attentions
        ).to(self.device)
        self._model.eval()

    # ── Prompt assembly ──────────────────────────────────────────────────────

    PROMPT_TEMPLATE = (
        "[INST] You are a helpful assistant that answers questions based ONLY on the provided context.\n"
        "If the answer is not in the context, say \"I cannot find this information in the provided context.\"\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer based strictly on the context above: [/INST]"
    )

    def _build_prompt_and_ranges(
        self,
        retrieved_passages: List[str],
        query: str,
    ) -> Tuple[str, List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        Build the full prompt and identify token-index ranges for:
          - retrieved_token_ranges: one (start, end) per passage
          - parametric_token_ranges: BOS + instruction + query (everything else)
        """
        self._lazy_load()

        # Build the context block with a unique delimiter between passages so
        # we can locate each passage's span after tokenization.
        delim = "\n\n---\n\n"
        context = delim.join(retrieved_passages)

        prompt = self.PROMPT_TEMPLATE.format(context=context, question=query)

        # Token-align each passage independently by matching substrings in the
        # full tokenization.
        enc = self._tok(prompt, return_tensors="pt", add_special_tokens=True)
        offsets = self._tok(prompt, return_offsets_mapping=True, add_special_tokens=True)["offset_mapping"]

        retrieved_ranges: List[Tuple[int, int]] = []
        cursor = prompt.find("Context:\n") + len("Context:\n")
        for i, passage in enumerate(retrieved_passages):
            start_char = prompt.find(passage, cursor)
            if start_char < 0:
                continue
            end_char = start_char + len(passage)
            cursor = end_char
            # Map char range to token indices via offsets
            tok_start = next(
                (ti for ti, (s, e) in enumerate(offsets) if s >= start_char), None
            )
            tok_end = next(
                (ti for ti, (s, e) in enumerate(offsets) if s >= end_char), len(offsets)
            )
            if tok_start is None:
                continue
            retrieved_ranges.append((tok_start, tok_end))

        # Parametric range = all tokens that are NOT inside a retrieved range.
        n_input = enc["input_ids"].shape[-1]
        retrieved_mask = np.zeros(n_input, dtype=bool)
        for s, e in retrieved_ranges:
            retrieved_mask[s:e] = True
        parametric_idxs = np.where(~retrieved_mask)[0]
        if len(parametric_idxs):
            parametric_ranges = [(int(parametric_idxs[0]), int(parametric_idxs[-1]) + 1)]
        else:
            parametric_ranges = []

        return prompt, retrieved_ranges, parametric_ranges

    # ── Core analysis ───────────────────────────────────────────────────────

    @torch.no_grad()
    def analyze(
        self,
        retrieved_passages: List[str],
        query: str,
        max_new_tokens: int = 64,
        top_k_attribution: int = 5,
    ) -> AttentionAnalysis:
        """Generate, extract attentions, compute entropy + mass attribution."""
        self._lazy_load()

        prompt, retrieved_ranges, parametric_ranges = self._build_prompt_and_ranges(
            retrieved_passages, query
        )
        enc = self._tok(prompt, return_tensors="pt", add_special_tokens=True).to(self.device)
        n_input = enc["input_ids"].shape[-1]

        # Greedy generation with return_dict_in_generate so we get per-step attentions
        gen = self._model.generate(
            **enc,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0,
            output_attentions=True,
            return_dict_in_generate=True,
        )

        sequences = gen.sequences                       # (1, n_input + n_new)
        output_ids = sequences[0, n_input:].tolist()
        output_text = self._tok.decode(output_ids, skip_special_tokens=True)

        # gen.attentions is a tuple of length n_new; each element is itself
        # a tuple of length n_layers of tensors shaped
        #   (batch, n_heads, query_len, key_len)
        # For step 0, query_len == n_input; for step t>0, query_len == 1.
        # We only need the last-row attention at each step (the generated token
        # attending back to input + previously generated tokens).
        n_new    = len(gen.attentions)
        if n_new == 0:
            # No tokens generated
            return AttentionAnalysis(
                prompt=prompt,
                output_text=output_text,
                input_token_count=n_input,
                output_token_count=0,
                retrieved_token_ranges=retrieved_ranges,
                parametric_token_ranges=parametric_ranges,
                attention_entropy=np.zeros((1, 1, 0)),
                retrieved_mass=np.zeros((1, 1, 0)),
                parametric_mass=np.zeros((1, 1, 0)),
            )

        n_layers = len(gen.attentions[0])
        n_heads  = gen.attentions[0][0].shape[1]

        entropy_arr       = np.zeros((n_layers, n_heads, n_new), dtype=np.float32)
        retrieved_mass_arr = np.zeros((n_layers, n_heads, n_new), dtype=np.float32)
        parametric_mass_arr = np.zeros((n_layers, n_heads, n_new), dtype=np.float32)

        per_tok_topk: List[List[Dict]] = []

        for step, layer_tuple in enumerate(gen.attentions):
            step_topk_per_layer: List[Dict] = []
            for layer_idx, attn in enumerate(layer_tuple):
                # attn shape: (1, n_heads, query_len, key_len)
                # key_len = n_input + step (prior outputs also attended to)
                last_row = attn[0, :, -1, :]   # (n_heads, key_len)

                # Restrict to input tokens only (we analyze attention to prompt)
                attn_np = last_row[:, :n_input].detach().to("cpu", dtype=torch.float32).numpy()
                attn_np = attn_np / (attn_np.sum(axis=-1, keepdims=True) + 1e-9)

                # Entropy per head
                ent = -np.sum(attn_np * np.log(attn_np + 1e-9), axis=-1)   # (n_heads,)
                entropy_arr[layer_idx, :, step] = ent

                # Retrieved vs parametric mass
                if retrieved_ranges:
                    rmass = np.zeros(n_heads, dtype=np.float32)
                    for s, e in retrieved_ranges:
                        rmass += attn_np[:, s:e].sum(axis=-1)
                    retrieved_mass_arr[layer_idx, :, step] = rmass
                    parametric_mass_arr[layer_idx, :, step] = 1.0 - rmass
                else:
                    retrieved_mass_arr[layer_idx, :, step] = np.nan
                    parametric_mass_arr[layer_idx, :, step] = np.nan

                # Top-k attribution: averaged over heads at this layer, pick top-k
                # input tokens. We only record the *last* layer's top-k to keep
                # output size manageable.
                if layer_idx == n_layers - 1:
                    head_avg = attn_np.mean(axis=0)        # (n_input,)
                    top_idx  = np.argsort(-head_avg)[:top_k_attribution]
                    top_list = []
                    for ti in top_idx.tolist():
                        in_retrieved = any(s <= ti < e for s, e in retrieved_ranges)
                        top_list.append({
                            "token_index": int(ti),
                            "prob":        float(head_avg[ti]),
                            "source":      "retrieved" if in_retrieved else "parametric",
                        })
                    step_topk_per_layer = top_list
            per_tok_topk.append(step_topk_per_layer)

        return AttentionAnalysis(
            prompt=prompt,
            output_text=output_text,
            input_token_count=n_input,
            output_token_count=n_new,
            retrieved_token_ranges=retrieved_ranges,
            parametric_token_ranges=parametric_ranges,
            attention_entropy=entropy_arr,
            retrieved_mass=retrieved_mass_arr,
            parametric_mass=parametric_mass_arr,
            top_k_attribution=per_tok_topk,
        )


def entropy_of(dist: np.ndarray) -> float:
    """Standalone helper for use in tests/scripts."""
    dist = np.asarray(dist, dtype=float)
    dist = dist / (dist.sum() + 1e-9)
    return float(-np.sum(dist * np.log(dist + 1e-9)))
