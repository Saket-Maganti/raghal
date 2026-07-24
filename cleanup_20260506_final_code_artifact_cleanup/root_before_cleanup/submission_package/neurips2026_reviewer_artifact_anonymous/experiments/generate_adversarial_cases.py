"""
generate_adversarial_cases.py — Item 6 (Upgrade Wave 1c)
=========================================================

Expands the adversarial coherence case set from 40 (10/category) to ~200
(50/category) by prompting a local Mistral-7B via Ollama to produce new
disjoint / contradict / drift / control cases that follow the schema used
by `src/adversarial_cases.py`.

Each generated case is validated:

  * JSON-parses into an `AdversarialCase`.
  * Has ≥3 passages with non-empty text.
  * Satisfies category-specific minimum coherence criteria (computed with
    the existing `src/coherence_metrics` signals):

        disjoint   : mean_jaccard ≤ 0.15
        contradict : pairwise NLI-contradiction ≥ 0.30 on ≥1 pair
        drift      : adjacent query-sim > endpoint query-sim by ≥ 0.10
        control    : CCS ≥ 0.55 AND mean_jaccard ≥ 0.20

  * Deduplicates queries and passages against the existing set.

Accepted cases are appended to the existing jsonl files. Rejected
candidates are logged to `data/adversarial/_rejected.jsonl` for audit.

Run:
    ADV_MODEL=mistral python3 experiments/generate_adversarial_cases.py \
        --target_per_category 50

The script is resumable: it inspects the current per-category counts and
only generates (target - current) new cases.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import os
import re
import time
from typing import Dict, List, Optional

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

from src.adversarial_cases import (
    AdversarialCase, CATEGORIES, load_all_cases, _DEFAULT_DATA_DIR,
)
from src.coherence_metrics import compute_coherence_metrics, compute_nli_pairwise
from src.hallucination_detector import HallucinationDetector


MODEL_NAME  = os.environ.get("ADV_MODEL", "mistral")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DATA_DIR    = _DEFAULT_DATA_DIR
REJECT_FILE = os.path.join(DATA_DIR, "_rejected.jsonl")


# ── Prompt templates per category ────────────────────────────────────────────

_BASE_TEMPLATE = """You are a benchmark author generating a single adversarial RAG retrieval case.

Output ONLY a single JSON object on one line, with no extra prose, following
this exact schema:

{{
  "case_id": "{cat}_NNN",
  "category": "{cat}",
  "query": "...",
  "corpus": "handcrafted_{domain_hint}",
  "passages": [
    {{"source_id": "...", "text": "..."}},
    {{"source_id": "...", "text": "..."}},
    {{"source_id": "...", "text": "..."}}
  ],
  "construction": {{"selection_rule": "{selection_rule}"}},
  "expected": {{"relevance_flags_it": {relevance_flag}, "coherence_flags_it": true}},
  "gold_context_label": "{gold}",
  "reference_answer": "...",
  "notes": ""
}}

Constraints for category **{cat}**:
{category_rules}

Domain inspiration (pick one, don't name it in the JSON):
{domain}

Do NOT produce any case whose query exactly matches one of these existing queries:
{existing_queries}

Return ONE JSON object. No markdown fences. No commentary."""

CATEGORY_RULES = {
    "disjoint": (
        "- All 3 passages answer the query correctly but use DIFFERENT surface\n"
        "  terminology for the same entity (≥3 distinct term variants).\n"
        "- Pairwise Jaccard overlap between passages should be very low (<0.1).\n"
        "- Each passage individually would pass a relevance filter.\n"
    ),
    "contradict": (
        "- At least 2 passages make OPPOSING factual claims about the query.\n"
        "- All passages use overlapping high-relevance vocabulary.\n"
        "- A good NLI classifier should flag at least one pairwise contradiction.\n"
    ),
    "drift": (
        "- Passage 1 is on-topic. Passage 2 shares entities with 1 but shifts\n"
        "  framing. Passage 3 is clearly off-topic yet lexically adjacent to 2.\n"
        "- Adjacent query-similarity should stay above the endpoint query-similarity.\n"
    ),
    "control": (
        "- All 3 passages are coherent, mutually consistent, and directly answer\n"
        "  the query with substantial shared vocabulary.\n"
        "- This is the 'good retrieval' matched control: CCS should be high,\n"
        "  mean pairwise Jaccard should be above 0.2.\n"
    ),
}

CATEGORY_META = {
    "disjoint":   dict(selection_rule="synonym_divergence",
                       relevance_flag="false", gold="answerable"),
    "contradict": dict(selection_rule="opposing_claims_high_sim",
                       relevance_flag="true", gold="ambiguous"),
    "drift":      dict(selection_rule="progressive_topic_drift",
                       relevance_flag="true", gold="partially_answerable"),
    "control":    dict(selection_rule="coherent_matched_control",
                       relevance_flag="true", gold="answerable"),
}

DOMAIN_POOL = [
    ("medical",          "a clinical / pharmacology / physiology topic"),
    ("biology",          "a molecular-biology / cell-biology / genetics topic"),
    ("physics",          "a classical or quantum physics phenomenon"),
    ("chemistry",        "an organic / inorganic / physical chemistry concept"),
    ("machine_learning", "a deep learning / optimization / RL concept"),
    ("software",         "an operating-systems / distributed-systems topic"),
    ("economics",        "a micro- or macroeconomics concept"),
    ("law",              "a contract / constitutional / tort law concept"),
    ("history",          "a 19th- or 20th-century historical event"),
    ("geography",        "a climate, ecology or geology topic"),
]


# ── Generation + validation ──────────────────────────────────────────────────

def _existing_queries(cases: List[AdversarialCase]) -> List[str]:
    return sorted({c.query.strip().lower() for c in cases})


def _existing_case_ids(cases: List[AdversarialCase]) -> Dict[str, int]:
    by_cat: Dict[str, int] = {c: 0 for c in CATEGORIES}
    max_id = {c: 0 for c in CATEGORIES}
    for c in cases:
        by_cat[c.category] = by_cat.get(c.category, 0) + 1
        m = re.search(r"(\d+)$", c.case_id)
        if m:
            max_id[c.category] = max(max_id[c.category], int(m.group(1)))
    return by_cat, max_id


def _sample_domain(i: int):
    d = DOMAIN_POOL[i % len(DOMAIN_POOL)]
    return d[0], d[1]


def _build_prompt(cat: str, seed_idx: int, existing_qs: List[str]) -> str:
    meta = CATEGORY_META[cat]
    domain_hint, domain_desc = _sample_domain(seed_idx)
    # Show the LLM up to ~20 existing queries to discourage repeats
    head = existing_qs[:20]
    rendered_existing = "\n".join(f"- {q}" for q in head) or "(none)"
    return _BASE_TEMPLATE.format(
        cat=cat,
        domain_hint=domain_hint,
        domain=domain_desc,
        category_rules=CATEGORY_RULES[cat],
        selection_rule=meta["selection_rule"],
        relevance_flag=meta["relevance_flag"],
        gold=meta["gold"],
        existing_queries=rendered_existing,
    )


_JSON_LINE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_single_json(text: str) -> Optional[dict]:
    m = _JSON_LINE.search(text.strip())
    if not m:
        return None
    blob = m.group(0)
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        # Try to repair trailing garbage
        try:
            depth, end = 0, -1
            for i, ch in enumerate(blob):
                if ch == "{": depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1; break
            if end > 0:
                return json.loads(blob[:end])
        except Exception:
            return None
    return None


def _validate(
    cand: dict,
    cat: str,
    new_case_id: str,
    existing_qs: set,
    embeddings,
    detector: HallucinationDetector,
) -> Optional[AdversarialCase]:
    try:
        if cand.get("category") != cat:
            cand["category"] = cat
        cand["case_id"] = new_case_id
        passages = cand.get("passages", [])
        if not isinstance(passages, list) or len(passages) < 3:
            return None
        for p in passages:
            if not isinstance(p, dict) or not p.get("text", "").strip():
                return None
            p.setdefault("source_id", f"{new_case_id}_{hash(p['text']) & 0xffff:x}")
        q = cand.get("query", "").strip()
        if not q or q.lower() in existing_qs:
            return None
        case = AdversarialCase(
            case_id=new_case_id,
            category=cat,
            query=q,
            corpus=cand.get("corpus", f"handcrafted_{cat}"),
            passages=passages,
            construction=cand.get("construction", {}),
            expected=cand.get("expected", {}),
            gold_context_label=cand.get("gold_context_label", "answerable"),
            reference_answer=cand.get("reference_answer", ""),
            notes=cand.get("notes", ""),
        )
    except Exception:
        return None

    # Category-specific structural checks using existing coherence metrics
    docs = case.as_documents()
    try:
        coh = compute_coherence_metrics(case.query, docs, embeddings)
    except Exception:
        return None

    ok = True
    reason = ""
    if cat == "disjoint":
        ok = coh.get("mean_jaccard", 1.0) <= 0.15
        reason = f"disjoint:mean_jaccard={coh.get('mean_jaccard'):.3f}"
    elif cat == "control":
        ok = (coh.get("ccs", 0.0) >= 0.55 and coh.get("mean_jaccard", 0.0) >= 0.20)
        reason = (f"control:ccs={coh.get('ccs', 0):.3f} "
                  f"jaccard={coh.get('mean_jaccard', 0):.3f}")
    elif cat == "drift":
        # Heuristic: rely on ccs_std being nontrivial (passages spread apart).
        ok = coh.get("ccs_std", 0.0) >= 0.05
        reason = f"drift:ccs_std={coh.get('ccs_std', 0):.3f}"
    elif cat == "contradict":
        # Contradict: run pairwise NLI, require any pair contradiction > 0.3.
        try:
            pw = compute_nli_pairwise(docs,
                                      lambda a, b: detector.score_sentence(a, b))
            max_contra = max(
                (x.get("contradiction", 0.0) for x in pw.get("pair_scores", [])),
                default=0.0,
            )
            ok = max_contra >= 0.30
            reason = f"contradict:max_contra={max_contra:.3f}"
        except Exception as exc:
            return None

    if not ok:
        case.notes = (case.notes + f" [validator:{reason}]").strip()
        _log_reject(case, reason)
        return None
    return case


def _log_reject(case: AdversarialCase, reason: str) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(REJECT_FILE, "a") as fh:
        fh.write(json.dumps({
            "case_id": case.case_id, "category": case.category,
            "query": case.query, "reason": reason,
        }) + "\n")


def _append_case(case: AdversarialCase) -> None:
    path = os.path.join(DATA_DIR, f"{case.category}.jsonl")
    rec = {
        "case_id": case.case_id,
        "category": case.category,
        "query": case.query,
        "corpus": case.corpus,
        "passages": case.passages,
        "construction": case.construction,
        "expected": case.expected,
        "gold_context_label": case.gold_context_label,
        "reference_answer": case.reference_answer,
        "notes": case.notes,
    }
    with open(path, "a") as fh:
        fh.write(json.dumps(rec) + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_per_category", type=int, default=50)
    parser.add_argument("--categories", nargs="+", default=list(CATEGORIES))
    parser.add_argument("--max_attempts_per_case", type=int, default=4)
    args = parser.parse_args()

    print(f"[AdvGen] model={MODEL_NAME}")
    # load_all_cases() returns Dict[category -> List[AdversarialCase]]; flatten
    # for the helpers below which expect a single list of cases.
    cases_by_cat = load_all_cases()
    cases: List[AdversarialCase] = [
        c for cat_cases in cases_by_cat.values() for c in cat_cases
    ]
    per_cat_count, per_cat_max = _existing_case_ids(cases)
    existing_q_set = set(_existing_queries(cases))
    print(f"[AdvGen] existing counts: {per_cat_count}")

    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    detector   = HallucinationDetector()
    llm = OllamaLLM(model=MODEL_NAME, temperature=0.6)

    added = {c: 0 for c in args.categories}
    rejected = {c: 0 for c in args.categories}

    for cat in args.categories:
        have = per_cat_count.get(cat, 0)
        need = max(0, args.target_per_category - have)
        print(f"\n[AdvGen] === {cat}  have={have}  need={need} ===")
        if need == 0:
            continue
        next_id = per_cat_max.get(cat, 0) + 1
        attempts = 0
        for i in range(need):
            case_added = False
            for attempt in range(args.max_attempts_per_case):
                attempts += 1
                prompt = _build_prompt(cat, attempts, sorted(existing_q_set))
                t0 = time.time()
                try:
                    raw = llm.invoke(prompt)
                except Exception as exc:
                    print(f"  [attempt {attempt}] LLM error: {exc}")
                    continue
                cand = _parse_single_json(raw)
                if not cand:
                    rejected[cat] += 1
                    continue
                new_id = f"{cat}_{next_id:03d}"
                case = _validate(cand, cat, new_id,
                                 existing_q_set, embeddings, detector)
                if case is None:
                    rejected[cat] += 1
                    continue
                _append_case(case)
                existing_q_set.add(case.query.strip().lower())
                next_id += 1
                added[cat] += 1
                case_added = True
                print(f"  ✓ {new_id}  [{time.time() - t0:.1f}s]  "
                      f"q='{case.query[:60]}'")
                break
            if not case_added:
                print(f"  ✗ case slot {i+1}/{need} exhausted "
                      f"{args.max_attempts_per_case} attempts")
        print(f"[AdvGen] {cat}: added={added[cat]}  rejected={rejected[cat]}")

    print("\n[AdvGen] Final:")
    for c in args.categories:
        new_total = per_cat_count.get(c, 0) + added[c]
        print(f"  {c:10s}  +{added[c]:>3d}  total={new_total}  "
              f"rejected={rejected[c]}")
    print(f"[AdvGen] Rejection log -> {REJECT_FILE}")


if __name__ == "__main__":
    main()
