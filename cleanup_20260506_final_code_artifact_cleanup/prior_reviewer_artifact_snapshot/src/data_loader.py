"""
Data Loader using SQuAD dataset
"""

from datasets import load_dataset
from langchain_core.documents import Document
from tqdm import tqdm


def load_qasper(split: str = "validation", max_papers: int = 50) -> tuple[list[Document], list[dict]]:
    print(f"[Data] Loading SQuAD ({split}, max_papers={max_papers})...")
    dataset = load_dataset("rajpurkar/squad", split=split)

    context_map = {}
    for item in dataset:
        ctx = item["context"]
        if ctx not in context_map:
            context_map[ctx] = {"context": ctx, "qas": []}
        context_map[ctx]["qas"].append({
            "question": item["question"],
            "answer": item["answers"]["text"][0] if item["answers"]["text"] else ""
        })

    contexts = list(context_map.values())[:max_papers]
    documents = []
    qa_pairs = []

    for i, entry in enumerate(contexts):
        doc = Document(
            page_content=entry["context"],
            metadata={"paper_id": str(i), "title": entry["context"][:60]}
        )
        documents.append(doc)
        for qa in entry["qas"]:
            if qa["answer"]:
                qa_pairs.append({
                    "paper_id": str(i),
                    "question": qa["question"],
                    "ground_truth": qa["answer"]
                })

    print(f"[Data] Loaded {len(documents)} contexts, {len(qa_pairs)} QA pairs")
    return documents, qa_pairs