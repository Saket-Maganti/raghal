"""
scripts/build_benchmark_v2.py — release builder for the expanded benchmark
===========================================================================

Produces `release/context_coherence_bench_v2/` from the current state of
`data/adversarial/*.jsonl` and `results/multidataset/coherence_paradox.csv`.
Mirrors the v1 packager (`release/context_coherence_bench_v1/`) but
includes:

    • The 200-case adversarial set (after the 40→200 expansion finishes)
    • Refreshed coherence_paradox.csv with whatever new (dataset, model)
      tuples have landed since v1
    • Updated metadata.json with new sha256 digests
    • Updated README.md stating "v2 = v1 + adversarial expansion"

Run after the expansion experiment finishes:

    python3 experiments/generate_adversarial_cases.py --target_per_category 50
    python3 scripts/build_benchmark_v2.py
    # → release/context_coherence_bench_v2/ ready to upload to HuggingFace

Usage
-----
    python3 scripts/build_benchmark_v2.py [--min_cases_per_category 40]

If any category has fewer than `--min_cases_per_category` cases we refuse
to cut the release (safer than shipping a half-expanded bundle).  Lower
the threshold to force anyway.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
ADV_DIR = ROOT / "data" / "adversarial"
PARADOX_CSV = ROOT / "results" / "multidataset" / "coherence_paradox.csv"
DEFAULT_DEST = ROOT / "release" / "context_coherence_bench_v2"

CATEGORIES = ["disjoint", "contradict", "drift", "control"]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return sum(1 for line in fh if line.strip())


def build(dest: Path, min_per_cat: int) -> None:
    print(f"[v2] staging into {dest}")

    # Sanity: all four adversarial files exist with enough cases.
    counts: Dict[str, int] = {}
    for cat in CATEGORIES:
        p = ADV_DIR / f"{cat}.jsonl"
        n = _count_jsonl(p)
        counts[cat] = n
        if n < min_per_cat:
            raise SystemExit(
                f"[v2] refusing to cut release: {cat}.jsonl has {n} cases "
                f"(need ≥ {min_per_cat}). Run "
                f"`python3 experiments/generate_adversarial_cases.py "
                f"--target_per_category {min_per_cat // 4 + 50}` first, "
                f"or pass --min_cases_per_category {n}."
            )
    total = sum(counts.values())
    print(f"[v2] adversarial case counts: {counts} (total {total})")

    # Sanity: paradox CSV exists.
    if not PARADOX_CSV.exists():
        raise SystemExit(f"[v2] missing {PARADOX_CSV} — run multidataset "
                         f"validation first.")

    # Wipe and recreate dest.
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "adversarial").mkdir(parents=True)
    (dest / "coherence_paradox").mkdir(parents=True)

    # Copy files + compute sha256.
    adv_entries: List[Dict] = []
    for cat in CATEGORIES:
        src = ADV_DIR / f"{cat}.jsonl"
        dst = dest / "adversarial" / f"{cat}.jsonl"
        shutil.copy2(src, dst)
        adv_entries.append({
            "src": str(src),
            "dst": str(dst.relative_to(ROOT)),
            "bytes": dst.stat().st_size,
            "sha256": _sha256(dst),
            "category": cat,
            "n_cases": counts[cat],
        })

    pg_dst = dest / "coherence_paradox" / "coherence_paradox.csv"
    shutil.copy2(PARADOX_CSV, pg_dst)

    # Copy static v1 files (LICENSE, CITATION.bib) as-is so v2 is standalone.
    v1 = ROOT / "release" / "context_coherence_bench_v1"
    for name in ("LICENSE", "CITATION.bib"):
        src = v1 / name
        if src.exists():
            shutil.copy2(src, dest / name)

    # Leaderboard YAML: copy v1's if present (users will append via PR).
    lb = v1 / "leaderboard.yaml"
    if lb.exists():
        shutil.copy2(lb, dest / "leaderboard.yaml")

    # Metadata
    meta = {
        "name": "ContextCoherenceBench",
        "version": "v2",
        "packaged_at": dt.datetime.now(dt.timezone.utc)
                        .isoformat(timespec="seconds").replace("+00:00", "Z"),
        "changelog_vs_v1": {
            "adversarial_total": total,
            "adversarial_v1_total": 40,
            "paradox_rows": sum(1 for _ in PARADOX_CSV.open()) - 1,
        },
        "subsets": [
            {"kind": "adversarial_coherence", "files": adv_entries},
            {"kind": "coherence_paradox", "files": [{
                "src": str(PARADOX_CSV),
                "dst": str(pg_dst.relative_to(ROOT)),
                "bytes": pg_dst.stat().st_size,
                "sha256": _sha256(pg_dst),
            }]},
        ],
    }
    with (dest / "metadata.json").open("w") as fh:
        json.dump(meta, fh, indent=2)

    # README
    readme = f"""\
# ContextCoherenceBench v2

Expansion of the v1 benchmark released alongside the NeurIPS 2026 submission
*"The Coherence Paradox in Retrieval-Augmented Generation"*.

## What changed vs v1

- **Adversarial cases**: {counts.get('disjoint', 0) + counts.get('contradict', 0) + counts.get('drift', 0) + counts.get('control', 0)} total
  (was 40 in v1). Per category:
{chr(10).join(f"    - {cat}: {counts[cat]}" for cat in CATEGORIES)}
- **Coherence paradox CSV**: refreshed on {meta['packaged_at']} UTC with all
  currently-completed (dataset, model) tuples from
  `results/multidataset/coherence_paradox.csv`.

## Layout

```
context_coherence_bench_v2/
├── README.md
├── LICENSE
├── CITATION.bib
├── metadata.json            # sha256 digests for every file
├── leaderboard.yaml         # community-submitted results
├── adversarial/
│   ├── disjoint.jsonl
│   ├── contradict.jsonl
│   ├── drift.jsonl
│   └── control.jsonl
└── coherence_paradox/
    └── coherence_paradox.csv
```

## Loading

```python
from datasets import load_dataset
ds = load_dataset("json", data_files={{
    "disjoint":   "adversarial/disjoint.jsonl",
    "contradict": "adversarial/contradict.jsonl",
    "drift":      "adversarial/drift.jsonl",
    "control":    "adversarial/control.jsonl",
}})
```

See `CITATION.bib` for how to cite.
"""
    (dest / "README.md").write_text(readme)

    print(f"[v2] ✅ wrote {dest}")
    print(f"[v2] total adversarial cases: {total}")
    print(f"[v2] next: zip + upload, e.g.")
    print(f"     cd release && zip -r context_coherence_bench_v2.zip "
          f"context_coherence_bench_v2")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", default=str(DEFAULT_DEST))
    ap.add_argument("--min_cases_per_category", type=int, default=40,
                    help="refuse to build if any category has fewer cases "
                         "(default 40 = barely-post-expansion floor)")
    args = ap.parse_args()
    build(Path(args.dest).resolve(), args.min_cases_per_category)


if __name__ == "__main__":
    main()
