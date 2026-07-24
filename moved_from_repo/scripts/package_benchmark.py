"""
package_benchmark.py — Item C1 (public benchmark release)
=========================================================

Bundles the artifacts needed to release `ContextCoherenceBench` as a
HuggingFace dataset + GitHub release. The benchmark ships three tasks:

    1. adversarial_coherence
       - 40 hand-authored cases (10 disjoint / 10 contradict / 10 drift /
         10 control) with labeled fragmentation categories and matched
         questions. Target metric: per-signal detection AUC.

    2. coherence_paradox
       - The 6-dataset query set + per-query coherence / faithfulness
         measurements for {baseline, hcpc_v1, hcpc_v2, crag, selfrag}.
         Target metric: paradox_drop (hcpc_v1 vs baseline) and v2_recovery
         (hcpc_v2 vs hcpc_v1).

    3. human_faithfulness
       - 500 double-annotated (case, condition) items with binary
         faithfulness + 1-5 correctness + 1-5 helpfulness ratings. Target
         metric: NLI ↔ human Spearman correlation + Fleiss' kappa.

Outputs to --output_dir (default: release/context_coherence_bench_v1/):

    adversarial/{disjoint,contradict,drift,control}.jsonl
    coherence_paradox/{per_query.csv, summary.csv}
    human_faithfulness/{aggregated.csv, manifest.csv}
    README.md                (HuggingFace dataset card)
    CITATION.bib
    LICENSE                  (CC-BY-4.0 for the hand-authored cases,
                              inherited per-dataset licenses for the rest)
    metadata.json            (schema + provenance)

Usage:
    python3 scripts/package_benchmark.py \\
        --adversarial_dir data/adversarial \\
        --paradox_csv results/multidataset/per_query.csv \\
        --paradox_summary_csv results/multidataset/summary.csv \\
        --human_aggregated results/human_validation/study_v1/aggregated_annotations.csv \\
        --human_manifest results/human_validation/study_v1/sample_manifest.csv \\
        --output_dir release/context_coherence_bench_v1

If a particular input is absent the corresponding subset is skipped with a
warning so the script can be run incrementally as runs complete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

DEFAULT_OUTPUT = "release/context_coherence_bench_v1"

README_TEMPLATE = """\
---
language:
  - en
license: cc-by-4.0
task_categories:
  - question-answering
  - text-classification
tags:
  - rag
  - retrieval-augmented-generation
  - hallucination
  - faithfulness
  - context-coherence
pretty_name: ContextCoherenceBench v1
size_categories:
  - n<1K
---

# ContextCoherenceBench v1

Companion benchmark for *“When Retrieval Improvements Hurt: Context
Coherence and Faithfulness in Retrieval-Augmented Generation.”*

The benchmark targets a specific empirical regularity we call the
**context coherence paradox**: naive retrieval improvements that raise
per-passage relevance can *lower* generation faithfulness because the
resulting passage set is more fragmented. ContextCoherenceBench lets other
researchers reproduce that effect on their own retrievers / generators and
compare against our selective-refinement baseline (HCPC-v2) as well as
Self-RAG and CRAG.

## Tasks

### 1. `adversarial_coherence`
- **N = 40** hand-authored cases.
- Four subsets:
  - `disjoint.jsonl` (10): passages all relevant to the query but drawn
    from disjoint topical neighborhoods.
  - `contradict.jsonl` (10): relevant passages containing contradictory
    claims about the queried entity.
  - `drift.jsonl` (10): passages that drift from a near-miss topic to the
    true target.
  - `control.jsonl` (10): matched coherent controls.
- **Schema** (one JSON per line):
  ```
  {{
    "case_id":  str,
    "category": "disjoint"|"contradict"|"drift"|"control",
    "question": str,
    "passages": [str, ...],
    "expected_failure_mode": str,
    "notes":    str
  }}
  ```
- **Target metric**: per-signal detection AUC across {{mean_query_chunk_sim,
  CCS, mean_jaccard, embedding_variance, retrieval_entropy, sim_spread,
  nli_pairwise_\\{{mean,max,frac_hi\\}}}}. See Table 4 in the paper.

### 2. `coherence_paradox`
- **N ≈ {paradox_n}** queries across six datasets (SQuAD, PubMedQA,
  NaturalQuestions, TriviaQA, HotpotQA, FinanceBench).
- **Conditions**: baseline, hcpc_v1, hcpc_v2, crag, selfrag.
- **Schema**: `per_query.csv` columns —
  `dataset, condition, question, ground_truth, answer,
   faithfulness_score, is_hallucination, mean_retrieval_similarity,
   latency_s`.
- **Target metric**: paradox_drop = faith(baseline) − faith(hcpc_v1);
  v2_recovery = faith(hcpc_v2) − faith(hcpc_v1).

### 3. `human_faithfulness`
- **N = {human_n}** (case, condition) items, 2 annotators each via
  Prolific (1000 annotation tasks).
- **Schema**: `aggregated.csv` —
  `task_id, n_annotations, human_faithful_rate, majority_faithful,
   mean_correctness, mean_helpfulness, any_disagreement`.
  Joined with `manifest.csv` for condition / NLI / provenance.
- **Target metric**: Fleiss' kappa (binary + ordinal) and Spearman
  rho(NLI faithfulness, human_faithful_rate).

## Provenance
- Adversarial cases: authored by the paper author; CC-BY-4.0.
- Coherence-paradox queries: drawn from the upstream datasets under their
  original licenses; see `metadata.json` for per-dataset details.
- Human annotations: collected on Prolific under IRB-exempt protocol
  (described in §6.X). Annotator IDs are redacted to `A<n>`.

## Loading

```python
from datasets import load_dataset

# Adversarial subset
adv = load_dataset("<hf-namespace>/context-coherence-bench",
                    name="adversarial_coherence")

# Coherence-paradox subset
par = load_dataset("<hf-namespace>/context-coherence-bench",
                    name="coherence_paradox")
```

## Baselines

Reproduction scripts ship in the companion GitHub repo:

```
git clone https://github.com/<anonymized>/context-coherence-bench
python3 experiments/run_adversarial_coherence.py
python3 experiments/run_multidataset_validation.py
python3 experiments/run_headtohead_comparison.py
```

## Citation

```bibtex
{citation}
```

Version: v1  (packaged {packaged_at})
"""

CITATION_TEMPLATE = """\
@inproceedings{maganti2026coherence,
  title     = {When Retrieval Improvements Hurt: Context Coherence and
               Faithfulness in Retrieval-Augmented Generation},
  author    = {Maganti, Saket},
  booktitle = {Proceedings of EMNLP / ACL 2026 (under review)},
  year      = {2026},
}
"""

LICENSE_TEXT = """\
Hand-authored content (data/adversarial/*.jsonl) is released under
Creative Commons Attribution 4.0 International (CC-BY-4.0).

Derived data drawn from SQuAD, PubMedQA, NaturalQuestions, TriviaQA,
HotpotQA and FinanceBench inherits the license of the upstream source.
See metadata.json for per-dataset license / citation information.
"""


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _copy(src: str, dst: str) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return {
        "src":     os.path.abspath(src),
        "dst":     os.path.relpath(dst),
        "bytes":   os.path.getsize(dst),
        "sha256":  _sha256(dst),
    }


def _count_lines(path: str) -> int:
    with open(path) as fh:
        return sum(1 for _ in fh)


def _count_csv_rows(path: str) -> int:
    import csv
    with open(path) as fh:
        return max(0, sum(1 for _ in csv.reader(fh)) - 1)


def package_adversarial(src_dir: str, out_dir: str) -> Dict[str, Any]:
    subset = {"kind": "adversarial_coherence", "files": [], "counts": {}}
    subsets = ["disjoint", "contradict", "drift", "control"]
    dest = os.path.join(out_dir, "adversarial")
    os.makedirs(dest, exist_ok=True)
    for name in subsets:
        src = os.path.join(src_dir, f"{name}.jsonl")
        if not os.path.exists(src):
            print(f"[bench] WARN: {src} missing")
            continue
        info = _copy(src, os.path.join(dest, f"{name}.jsonl"))
        info["category"] = name
        info["n_cases"]  = _count_lines(src)
        subset["files"].append(info)
        subset["counts"][name] = info["n_cases"]
    readme_src = os.path.join(src_dir, "README.md")
    if os.path.exists(readme_src):
        subset["files"].append(_copy(readme_src, os.path.join(dest, "README.md")))
    return subset


def package_paradox(per_query: Optional[str], summary: Optional[str],
                    out_dir: str) -> Dict[str, Any]:
    subset = {"kind": "coherence_paradox", "files": []}
    dest = os.path.join(out_dir, "coherence_paradox")
    if per_query and os.path.exists(per_query):
        info = _copy(per_query, os.path.join(dest, "per_query.csv"))
        info["n_rows"] = _count_csv_rows(per_query)
        subset["files"].append(info)
        subset["n_queries"] = info["n_rows"]
    else:
        print(f"[bench] WARN: paradox per-query CSV missing ({per_query})")
    if summary and os.path.exists(summary):
        subset["files"].append(_copy(summary, os.path.join(dest, "summary.csv")))
    return subset


def package_human(aggregated: Optional[str], manifest: Optional[str],
                  out_dir: str) -> Dict[str, Any]:
    subset = {"kind": "human_faithfulness", "files": []}
    dest = os.path.join(out_dir, "human_faithfulness")
    if aggregated and os.path.exists(aggregated):
        info = _copy(aggregated, os.path.join(dest, "aggregated.csv"))
        info["n_rows"] = _count_csv_rows(aggregated)
        subset["files"].append(info)
        subset["n_items"] = info["n_rows"]
    else:
        print(f"[bench] WARN: human aggregated CSV missing ({aggregated})")
    if manifest and os.path.exists(manifest):
        subset["files"].append(_copy(manifest, os.path.join(dest, "manifest.csv")))
    return subset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adversarial_dir",        default="data/adversarial")
    parser.add_argument("--paradox_csv",            default="results/multidataset/per_query.csv")
    parser.add_argument("--paradox_summary_csv",    default="results/multidataset/summary.csv")
    parser.add_argument("--human_aggregated",       default="results/human_validation/study_v1/aggregated_annotations.csv")
    parser.add_argument("--human_manifest",         default="results/human_validation/study_v1/sample_manifest.csv")
    parser.add_argument("--output_dir",             default=DEFAULT_OUTPUT)
    parser.add_argument("--version_tag",            default="v1")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    subsets = []
    subsets.append(package_adversarial(args.adversarial_dir, args.output_dir))
    subsets.append(package_paradox(args.paradox_csv, args.paradox_summary_csv,
                                    args.output_dir))
    subsets.append(package_human(args.human_aggregated, args.human_manifest,
                                  args.output_dir))

    paradox_n = next((s.get("n_queries", "TBD") for s in subsets
                      if s["kind"] == "coherence_paradox"), "TBD")
    human_n   = next((s.get("n_items",   "TBD") for s in subsets
                      if s["kind"] == "human_faithfulness"), "TBD")

    readme = README_TEMPLATE.format(
        paradox_n=paradox_n,
        human_n=human_n,
        citation=CITATION_TEMPLATE.strip(),
        packaged_at=datetime.utcnow().strftime("%Y-%m-%d"),
    )
    with open(os.path.join(args.output_dir, "README.md"), "w") as fh:
        fh.write(readme)
    with open(os.path.join(args.output_dir, "CITATION.bib"), "w") as fh:
        fh.write(CITATION_TEMPLATE)
    with open(os.path.join(args.output_dir, "LICENSE"), "w") as fh:
        fh.write(LICENSE_TEXT)

    metadata = {
        "name":        "ContextCoherenceBench",
        "version":     args.version_tag,
        "packaged_at": datetime.utcnow().isoformat() + "Z",
        "subsets":     subsets,
        "upstream_datasets": {
            "squad":          {"license": "CC-BY-SA-4.0", "url": "https://rajpurkar.github.io/SQuAD-explorer/"},
            "pubmedqa":       {"license": "MIT",          "url": "https://pubmedqa.github.io/"},
            "naturalqs":      {"license": "CC-BY-SA-3.0", "url": "https://ai.google.com/research/NaturalQuestions"},
            "triviaqa":       {"license": "Apache-2.0",   "url": "http://nlp.cs.washington.edu/triviaqa/"},
            "hotpotqa":       {"license": "CC-BY-SA-4.0", "url": "https://hotpotqa.github.io/"},
            "financebench":   {"license": "CC-BY-NC-4.0", "url": "https://github.com/patronus-ai/financebench"},
        },
        "paper_citation": CITATION_TEMPLATE.strip(),
    }
    with open(os.path.join(args.output_dir, "metadata.json"), "w") as fh:
        json.dump(metadata, fh, indent=2)

    print(f"[bench] packaged -> {args.output_dir}/")
    for s in subsets:
        n = len(s.get("files", []))
        print(f"  - {s['kind']}: {n} file(s)")


if __name__ == "__main__":
    main()
