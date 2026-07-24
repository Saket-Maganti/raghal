"""
src/dataset_loaders.py
Unified loader interface for the 6 datasets used in the multi-dataset
generalization study (§Results, expanded Table 2).

Loaders return (documents, qa_pairs) with a common schema:

  documents : List[Document]   page_content = passage / context, metadata = {paper_id, title}
  qa_pairs  : List[dict]       {paper_id, question, ground_truth}

Datasets:
  squad         — Wikipedia reading comprehension (existing, in data_loader)
  pubmedqa      — biomedical QA               (existing, in pubmedqa_loader)
  naturalqs     — Natural Questions (open-domain QA over Wikipedia)
  triviaqa      — TriviaQA (Wikipedia-validated trivia)
  hotpotqa      — multi-hop QA across multiple Wikipedia paragraphs
  financebench  — financial QA with SEC filings as context

For datasets we don't already have loaders for, this module wraps the
HuggingFace datasets library. FinanceBench is loaded from the official
PatronusAI release.

NOTE: Each loader caps at `max_papers` rows for tractable experimentation
and deterministic sampling (seed=42). The cap is applied after
deduplication of contexts to keep the document store small.
"""

from __future__ import annotations

import os
import random
from typing import Callable, Dict, List, Tuple

from langchain_core.documents import Document
from tqdm import tqdm

# Re-export the existing loaders for uniform access
from src.data_loader import load_qasper as _load_squad
from src.pubmedqa_loader import load_pubmedqa as _load_pubmedqa


SEED = 42


# ── Natural Questions ────────────────────────────────────────────────────────

def load_naturalqs(
    split: str = "validation",
    max_papers: int = 50,
) -> Tuple[List[Document], List[dict]]:
    """
    Natural Questions (open-domain). We use the simplified version curated by
    Google Research, which provides short answers and the Wikipedia document
    text. Many examples have null short answers; we keep only those with a
    valid short answer span.
    """
    from datasets import load_dataset
    print(f"[Data] Loading Natural Questions ({split})...")
    # Stream validation: the non-streaming path triggers a full train-split
    # generation (~55 GB, 287 parquets) and one bad shard raises
    # DatasetGenerationError, silently corrupting later iteration.
    try:
        ds = load_dataset("google-research-datasets/natural_questions",
                          "default", split=split, streaming=True)
    except Exception:
        # Fallback: the lighter "nq_open" subset (questions + answers, no docs)
        # paired with a separately loaded Wikipedia dump. We stub by skipping
        # context (callers will see empty passages).
        ds = load_dataset("nq_open", split="validation", streaming=True)

    docs: List[Document] = []
    qa: List[dict] = []
    rng = random.Random(SEED)
    items = list(ds)
    rng.shuffle(items)

    seen_contexts = {}
    for item in tqdm(items, desc="NQ"):
        question = item.get("question") or item.get("question_text", "")
        if isinstance(question, dict):
            question = question.get("text", "")
        if not question:
            continue

        # NQ default config: `annotations` is a dict whose `short_answers`
        # is a list-per-annotator (5 annotators). Most annotators leave
        # `text: []`; we keep the first annotator that supplied any text.
        ground_truth = ""
        if "annotations" in item:
            ann = item["annotations"]
            candidates = []
            if isinstance(ann, dict):
                candidates = ann.get("short_answers", []) or []
            elif isinstance(ann, list):
                for a in ann:
                    if isinstance(a, dict):
                        candidates.extend(a.get("short_answers", []) or [])
            for sa in candidates:
                if not isinstance(sa, dict):
                    continue
                txt = sa.get("text") or []
                if txt:
                    ground_truth = txt[0]
                    break
        elif "answer" in item:
            answer = item["answer"]
            if isinstance(answer, list) and answer:
                ground_truth = answer[0]
            elif isinstance(answer, str):
                ground_truth = answer
        if not ground_truth:
            continue

        # Context: try document.tokens then document.html stripped, else skip
        context = ""
        doc_obj = item.get("document", {})
        if isinstance(doc_obj, dict):
            toks = doc_obj.get("tokens", {})
            if isinstance(toks, dict) and toks.get("token"):
                # Filter HTML tokens
                tok_list = toks.get("token", [])
                is_html = toks.get("is_html", [False] * len(tok_list))
                context = " ".join(t for t, h in zip(tok_list, is_html) if not h)
        if not context:
            continue
        # Cap context length to keep ChromaDB manageable
        context = context[:8000]
        ctx_key = context[:200]
        if ctx_key in seen_contexts:
            paper_id = seen_contexts[ctx_key]
        else:
            paper_id = str(len(seen_contexts))
            seen_contexts[ctx_key] = paper_id
            docs.append(Document(page_content=context, metadata={
                "paper_id": paper_id, "title": question[:60]
            }))
        qa.append({
            "paper_id": paper_id,
            "question": question,
            "ground_truth": ground_truth,
        })
        if len(docs) >= max_papers:
            break

    print(f"[Data] NQ: {len(docs)} contexts, {len(qa)} QA pairs")
    return docs, qa


# ── TriviaQA ─────────────────────────────────────────────────────────────────

def load_triviaqa(
    split: str = "validation",
    max_papers: int = 50,
) -> Tuple[List[Document], List[dict]]:
    """
    TriviaQA, RC variant (questions paired with Wikipedia / web evidence).
    We use the rc.nocontext config and append the verified Wikipedia
    evidence text as context.
    """
    from datasets import load_dataset
    print(f"[Data] Loading TriviaQA ({split})...")
    ds = load_dataset("mandarjoshi/trivia_qa", "rc.wikipedia", split=split)

    docs: List[Document] = []
    qa: List[dict] = []
    rng = random.Random(SEED)
    items = list(ds)
    rng.shuffle(items)

    seen_contexts = {}
    for item in tqdm(items, desc="TriviaQA"):
        question = item.get("question", "")
        answer_obj = item.get("answer", {})
        ground_truth = ""
        if isinstance(answer_obj, dict):
            ground_truth = (answer_obj.get("value") or
                            (answer_obj.get("aliases") or [""])[0])
        if not (question and ground_truth):
            continue

        # entity_pages.wiki_context holds long-form Wikipedia evidence
        ent_pages = item.get("entity_pages", {})
        wiki_ctxs = ent_pages.get("wiki_context", []) if isinstance(ent_pages, dict) else []
        context = " ".join(wiki_ctxs)[:8000].strip() if wiki_ctxs else ""
        if not context:
            continue

        ctx_key = context[:200]
        if ctx_key in seen_contexts:
            paper_id = seen_contexts[ctx_key]
        else:
            paper_id = str(len(seen_contexts))
            seen_contexts[ctx_key] = paper_id
            docs.append(Document(page_content=context, metadata={
                "paper_id": paper_id, "title": question[:60]
            }))
        qa.append({
            "paper_id": paper_id,
            "question": question,
            "ground_truth": ground_truth,
        })
        if len(docs) >= max_papers:
            break

    print(f"[Data] TriviaQA: {len(docs)} contexts, {len(qa)} QA pairs")
    return docs, qa


# ── HotpotQA (multi-hop) ─────────────────────────────────────────────────────

def load_hotpotqa(
    split: str = "validation",
    max_papers: int = 50,
) -> Tuple[List[Document], List[dict]]:
    """
    HotpotQA distractor split: each example has 10 paragraphs, of which 2-3
    are 'gold' supporting evidence. We index ALL paragraphs (gold + distractors)
    as separate documents — this is the multi-hop generalization test for the
    coherence paradox: a correct answer requires retrieving and integrating
    multiple distinct passages.
    """
    from datasets import load_dataset
    print(f"[Data] Loading HotpotQA ({split})...")
    ds = load_dataset("hotpot_qa", "distractor", split=split, trust_remote_code=True)

    docs: List[Document] = []
    qa: List[dict] = []
    rng = random.Random(SEED)
    items = list(ds)
    rng.shuffle(items)

    paper_counter = 0
    for item in tqdm(items, desc="HotpotQA"):
        question = item.get("question", "")
        answer = item.get("answer", "")
        if not (question and answer):
            continue
        ctx_obj = item.get("context", {})
        titles = ctx_obj.get("title", []) if isinstance(ctx_obj, dict) else []
        sentences_per_title = ctx_obj.get("sentences", []) if isinstance(ctx_obj, dict) else []
        if not titles:
            continue

        # Each title's sentences become one Document
        for title, sents in zip(titles, sentences_per_title):
            content = " ".join(sents).strip()
            if not content:
                continue
            paper_id = f"{paper_counter}_{title[:40]}"
            docs.append(Document(page_content=content, metadata={
                "paper_id": paper_id, "title": title,
                "supports_question": question[:80],
            }))
            paper_counter += 1
        qa.append({
            "paper_id": str(paper_counter),
            "question": question,
            "ground_truth": answer,
            "supporting_titles": item.get("supporting_facts", {}).get("title", []),
            "is_multihop": True,
        })
        # Each HotpotQA example contributes ~10 paragraphs; cap on docs.
        if len(docs) >= max_papers * 10:
            break

    print(f"[Data] HotpotQA: {len(docs)} paragraphs, {len(qa)} multi-hop QA pairs")
    return docs, qa


# ── FinanceBench ─────────────────────────────────────────────────────────────

def load_financebench(
    split: str = "test",
    max_papers: int = 50,
) -> Tuple[List[Document], List[dict]]:
    """
    FinanceBench (Patronus AI release): financial QA over SEC filings.
    The dataset provides a `evidence` field with the relevant filing text and
    a `question` + `answer` pair. Each (filing, evidence) pair becomes one
    Document for indexing.
    """
    from datasets import load_dataset
    print(f"[Data] Loading FinanceBench ({split})...")
    try:
        ds = load_dataset("PatronusAI/financebench", split=split)
    except Exception as exc:
        print(
            f"[Data] FinanceBench load failed ({exc}); the dataset may be gated. "
            "Apply for access through the dataset provider."
        )
        return [], []

    docs: List[Document] = []
    qa: List[dict] = []
    rng = random.Random(SEED)
    items = list(ds)
    rng.shuffle(items)

    seen_contexts = {}
    for item in tqdm(items, desc="FinanceBench"):
        question = item.get("question", "")
        answer = item.get("answer", "")
        if not (question and answer):
            continue
        # The dataset exposes either `evidence` (list of dicts) or
        # `evidence_text` depending on version; handle both.
        evidence = ""
        if "evidence" in item:
            ev = item["evidence"]
            if isinstance(ev, list):
                evidence = " ".join(e.get("evidence_text", "") if isinstance(e, dict) else str(e) for e in ev)
            else:
                evidence = str(ev)
        elif "evidence_text" in item:
            evidence = item["evidence_text"] or ""
        if not evidence:
            continue
        evidence = evidence[:8000]
        ctx_key = evidence[:200]
        if ctx_key in seen_contexts:
            paper_id = seen_contexts[ctx_key]
        else:
            paper_id = str(len(seen_contexts))
            seen_contexts[ctx_key] = paper_id
            docs.append(Document(page_content=evidence, metadata={
                "paper_id": paper_id,
                "title":    item.get("doc_name", question)[:60],
            }))
        qa.append({
            "paper_id":     paper_id,
            "question":     question,
            "ground_truth": answer,
            "company":      item.get("company", ""),
            "doc_period":   item.get("doc_period", ""),
        })
        if len(docs) >= max_papers:
            break

    print(f"[Data] FinanceBench: {len(docs)} contexts, {len(qa)} QA pairs")
    return docs, qa


# ── Long-form QA datasets (Phase 2 Item 3) ──────────────────────────────────
#
# The five datasets above are all short-answer (extractive / yes-no / span).
# Reviewers commonly ask whether the coherence paradox generalizes to
# *long-form* generation tasks where the model must synthesize multi-sentence
# answers. These two loaders cover that gap:
#
#   qasper        — scientific-paper long-form QA (AllenAI)
#   msmarco       — MS-MARCO v2.1 long-form answer generation track
#
# Both expose the same (documents, qa_pairs) contract as the short-answer
# loaders, with `qa_pair["ground_truth"]` being a multi-sentence reference
# answer. The experiments/run_longform_eval.py runner treats them as
# long-form by computing ROUGE-L + per-claim NLI instead of single-span
# faithfulness.

_QASPER_URL = (
    "https://qasper-dataset.s3.us-west-2.amazonaws.com/"
    "qasper-train-dev-v0.3.tgz"
)
_QASPER_CACHE = os.path.expanduser("~/.cache/rag_hallu/qasper")


def _fetch_qasper(split: str) -> List[dict]:
    """Download QASPER tarball from AllenAI S3 and return parsed JSON items.

    The HF-hosted `allenai/qasper` dataset relies on a legacy `qasper.py`
    script that newer `datasets` releases refuse to execute.  Fetching the
    raw tarball directly from AllenAI is version-independent.
    """
    import json as _json
    import tarfile
    import urllib.request

    os.makedirs(_QASPER_CACHE, exist_ok=True)
    split_file = {
        "train":      "qasper-train-v0.3.json",
        "validation": "qasper-dev-v0.3.json",
    }.get(split, "qasper-dev-v0.3.json")
    cached = os.path.join(_QASPER_CACHE, split_file)

    if not os.path.exists(cached):
        tar_path = os.path.join(_QASPER_CACHE, "qasper.tgz")
        if not os.path.exists(tar_path):
            print(f"[Data] Downloading QASPER tarball (~20 MB) to {tar_path}")
            urllib.request.urlretrieve(_QASPER_URL, tar_path)
        with tarfile.open(tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith(split_file):
                    fh = tar.extractfile(member)
                    if fh is None:
                        continue
                    with open(cached, "wb") as out:
                        out.write(fh.read())
                    break

    if not os.path.exists(cached):
        return []
    with open(cached) as fh:
        blob = _json.load(fh)
    # Raw schema is {paper_id -> {title, abstract, full_text, qas}}.
    items: List[dict] = []
    for pid, body in blob.items():
        body = dict(body)
        body["id"] = pid
        items.append(body)
    return items


def load_qasper_longform(
    split: str = "validation",
    max_papers: int = 30,
) -> Tuple[List[Document], List[dict]]:
    """
    QASPER (Dasigi et al., NAACL 2021). Scientific-paper QA with free-form
    long answers and human-annotated evidence paragraphs.

    Raw data is fetched from AllenAI's S3 distribution on first call and
    cached under `~/.cache/rag_hallu/qasper/`.  This avoids HF `datasets`
    script-loader deprecation in recent releases.
    """
    print(f"[Data] Loading QASPER ({split}) via AllenAI S3 mirror...")
    try:
        items = _fetch_qasper(split)
    except Exception as exc:
        print(f"[Data] QASPER fetch failed ({exc})")
        return [], []
    if not items:
        print("[Data] QASPER: no items parsed")
        return [], []

    docs: List[Document] = []
    qa:   List[dict] = []
    rng = random.Random(SEED)
    rng.shuffle(items)

    for item in tqdm(items, desc="QASPER"):
        paper_id = str(item.get("id") or len(docs))
        title    = (item.get("title") or "")[:80]

        paper_docs_start = len(docs)

        # Abstract first (one Document per paper).
        abstract = (item.get("abstract") or "").strip()
        if len(abstract) >= 80:
            docs.append(Document(page_content=abstract[:4000], metadata={
                "paper_id": paper_id,
                "title":    title,
                "section":  "abstract",
            }))

        # Flatten full_text into paragraph-level Documents.
        for section in (item.get("full_text") or []):
            sec_name = (section or {}).get("section_name") or ""
            for p in (section or {}).get("paragraphs") or []:
                p = (p or "").strip()
                if len(p) < 80:
                    continue
                docs.append(Document(page_content=p[:4000], metadata={
                    "paper_id": paper_id,
                    "title":    title,
                    "section":  sec_name,
                }))

        # Collect QA pairs.
        for qa_block in (item.get("qas") or []):
            q = (qa_block or {}).get("question") or ""
            if not q:
                continue
            free_forms: List[str] = []
            for ans in (qa_block.get("answers") or []):
                a = (ans or {}).get("answer") or {}
                ff = (a.get("free_form_answer") or "").strip()
                if ff and ff.lower() not in ("yes", "no", "unanswerable", "none"):
                    free_forms.append(ff)
            if not free_forms:
                continue
            gt = max(free_forms, key=len)
            qa.append({
                "paper_id":     paper_id,
                "question":     q,
                "ground_truth": gt,
                "task":         "longform",
            })

        paper_ids_seen = {d.metadata["paper_id"] for d in docs}
        if len(paper_ids_seen) >= max_papers:
            # If this paper contributed docs but no QA pairs, drop its docs.
            if paper_docs_start < len(docs) and not any(
                x["paper_id"] == paper_id for x in qa
            ):
                del docs[paper_docs_start:]
            break

    print(f"[Data] QASPER: {len(docs)} paragraphs, {len(qa)} long-form QA pairs")
    return docs, qa


def load_msmarco_longform(
    split: str = "validation",
    max_papers: int = 40,
) -> Tuple[List[Document], List[dict]]:
    """
    MS-MARCO v2.1 (Nguyen et al., 2016) — long-form answer generation track.
    HF id: microsoft/ms_marco (config "v2.1").

    Schema:
        query                 : str
        passages.passage_text : list[str]     (10 candidate passages)
        passages.is_selected  : list[int]     (which passages were used)
        answers               : list[str]     (human long-form answers)

    We skip examples whose `answers` list is empty or contains only the
    string "No Answer Present.".
    """
    # Robust loader:
    #   1. Try v2.1 streaming with `.take(bounded)` so we never iterate past
    #      what we need — fixes the observed multi-minute stall on 2026-04-24.
    #   2. Per-example try/except so a single malformed row does not kill the
    #      whole stream.
    #   3. If v2.1 streaming returns zero usable examples within `hard_limit`
    #      candidates, fall back to v1.1 (~100 k dev split, smaller + more
    #      reliable for a 20-question evaluation).
    from datasets import load_dataset
    # Read ~5× max_papers candidates to account for filtered-out examples
    # (empty answers, "No Answer Present.", <80-char passages, dupes).
    hard_limit = max(200, max_papers * 8)

    def _iter_config(config: str):
        print(f"[Data] Loading MS-MARCO {config} ({split}, streaming, "
              f"bounded to {hard_limit} rows)...")
        try:
            ds = load_dataset(
                "microsoft/ms_marco", config, split=split, streaming=True,
            )
            return ds.take(hard_limit)
        except Exception as exc:
            print(f"[Data] MS-MARCO {config} load failed ({exc})")
            return None

    def _parse_stream(stream) -> Tuple[List[Document], List[dict]]:
        docs_: List[Document] = []
        qa_:   List[dict] = []
        seen_: set = set()
        if stream is None:
            return docs_, qa_
        for raw in tqdm(stream, desc="MS-MARCO", total=hard_limit):
            if len(seen_) >= max_papers:
                break
            try:
                query = (raw.get("query") or "").strip()
                answers = raw.get("answers") or []
                answers = [a.strip() for a in answers
                           if isinstance(a, str) and a.strip()]
                answers = [a for a in answers
                           if a.lower() != "no answer present."]
                if not (query and answers):
                    continue
                passages = raw.get("passages") or {}
                ptexts = passages.get("passage_text") or []
                if not ptexts:
                    continue
                paper_id = str(raw.get("query_id", len(seen_)))
                if paper_id in seen_:
                    continue
                seen_.add(paper_id)
                for p in ptexts:
                    p = (p or "").strip()
                    if len(p) < 80:
                        continue
                    docs_.append(Document(
                        page_content=p[:4000],
                        metadata={"paper_id": paper_id, "title": query[:80]},
                    ))
                gt = max(answers, key=len)
                qa_.append({
                    "paper_id":     paper_id,
                    "question":     query,
                    "ground_truth": gt,
                    "task":         "longform",
                })
            except Exception as exc:
                # Corrupted single row — skip without aborting the stream.
                print(f"[Data] MS-MARCO: skipped a malformed row ({exc})")
                continue
        return docs_, qa_

    # Try v2.1 first (paper default), fall back to v1.1 if empty.
    docs, qa = _parse_stream(_iter_config("v2.1"))
    if not qa:
        print("[Data] MS-MARCO v2.1 produced 0 usable examples "
              "— falling back to v1.1")
        docs, qa = _parse_stream(_iter_config("v1.1"))

    print(f"[Data] MS-MARCO: {len(docs)} passages, {len(qa)} long-form QA pairs")
    return docs, qa


# ── Unified registry ─────────────────────────────────────────────────────────

LoaderFn = Callable[[str, int], Tuple[List[Document], List[dict]]]

DATASET_REGISTRY: Dict[str, Dict] = {
    "squad": {
        "loader": _load_squad,
        "default_split": "validation",
        "domain": "general (Wikipedia)",
        "task_type": "single-hop extractive",
    },
    "pubmedqa": {
        "loader": _load_pubmedqa,
        "default_split": "train",
        "domain": "biomedical (PubMed abstracts)",
        "task_type": "single-hop yes/no/maybe",
    },
    "naturalqs": {
        "loader": load_naturalqs,
        "default_split": "validation",
        "domain": "general (Wikipedia, open-domain)",
        "task_type": "single-hop extractive",
    },
    "triviaqa": {
        "loader": load_triviaqa,
        "default_split": "validation",
        "domain": "general (Wikipedia, trivia)",
        "task_type": "single-hop extractive",
    },
    "hotpotqa": {
        "loader": load_hotpotqa,
        "default_split": "validation",
        "domain": "general (Wikipedia, multi-paragraph)",
        "task_type": "multi-hop reasoning",
    },
    "financebench": {
        "loader": load_financebench,
        "default_split": "test",
        "domain": "finance (SEC filings)",
        "task_type": "domain-specific factoid + numerical",
    },
    "qasper": {
        "loader": load_qasper_longform,
        "default_split": "validation",
        "domain": "scientific papers (NLP/ML)",
        "task_type": "long-form abstractive QA",
    },
    "msmarco": {
        "loader": load_msmarco_longform,
        "default_split": "validation",
        "domain": "open-domain web passages",
        "task_type": "long-form answer generation",
    },
}


def load_dataset_by_name(
    name: str,
    max_papers: int = 50,
    split: str = None,
) -> Tuple[List[Document], List[dict]]:
    if name not in DATASET_REGISTRY:
        raise ValueError(f"Unknown dataset {name!r}; choices = {list(DATASET_REGISTRY)}")
    spec = DATASET_REGISTRY[name]
    actual_split = split or spec["default_split"]
    return spec["loader"](split=actual_split, max_papers=max_papers)
