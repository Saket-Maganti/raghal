from datasets import load_dataset
from langchain_core.documents import Document
from tqdm import tqdm

def load_pubmedqa(split="train", max_papers=50):
    print(f"[Data] Loading PubMedQA ({split}, max_papers={max_papers})...")
    dataset = load_dataset("qiaojin/PubMedQA", "pqa_labeled", split=split)
    documents = []
    qa_pairs = []
    for i, item in enumerate(tqdm(list(dataset)[:max_papers], desc="Processing")):
        context = " ".join(item["context"]["contexts"])
        question = item["question"]
        answer = item["long_answer"]
        if not context or not question or not answer:
            continue
        from langchain_core.documents import Document
        doc = Document(page_content=context, metadata={"paper_id": str(i), "title": question[:60]})
        documents.append(doc)
        qa_pairs.append({"paper_id": str(i), "question": question, "ground_truth": answer})
    print(f"[Data] Loaded {len(documents)} contexts, {len(qa_pairs)} QA pairs")
    return documents, qa_pairs
