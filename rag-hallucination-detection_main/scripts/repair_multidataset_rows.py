"""
scripts/repair_multidataset_rows.py — row-count repair helper
==============================================================

Problem
-------
`results/multidataset/` has per-(dataset, model) CSVs that should all
have `n_questions × 3_conditions` rows.  Some earlier runs produced
uneven counts (e.g. NaturalQuestions: 90 / 217 / 149 across 3 models)
because a prior pipeline crash wrote a partial file, then the
`completed_tuples.json` checkpoint was marked true anyway.

This script:
    1. Audits every `{dataset}__{model}_per_query.csv`
    2. Flags files whose row count is not `expected_n` (default 90)
    3. For each mismatched file:
         - backs it up to `backups_YYYYMMDD/`
         - deletes the original
         - removes the corresponding entry from `completed_tuples.json`
    4. Prints the one-liner you need to re-run to fix the gap.

The repair is **non-destructive by default** — pass `--apply` to actually
delete.  Without `--apply` it's a dry run that reports what would happen.

Usage
-----
    # Inspect:
    python3 scripts/repair_multidataset_rows.py
    # Apply:
    python3 scripts/repair_multidataset_rows.py --apply
    # Custom expected count (if you changed n_questions):
    python3 scripts/repair_multidataset_rows.py --expected_rows 90 --apply
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MULTIDATASET_DIR = ROOT / "results" / "multidataset"
CHECKPOINT = MULTIDATASET_DIR / "completed_tuples.json"

PER_QUERY_RE = re.compile(r"^([a-z0-9_]+)__([a-z0-9.\-]+)_per_query\.csv$")


def _audit(expected_rows: int) -> List[Tuple[Path, str, str, int]]:
    """Return [(path, dataset, model, actual_rows), ...] for offending files."""
    bad: List[Tuple[Path, str, str, int]] = []
    for p in sorted(MULTIDATASET_DIR.glob("*_per_query.csv")):
        if p.name in ("per_query.csv",):        # skip concatenated
            continue
        m = PER_QUERY_RE.match(p.name)
        if not m:
            continue
        ds, mdl = m.group(1), m.group(2)
        try:
            df = pd.read_csv(p)
        except Exception as exc:
            print(f"[repair] {p.name}: read error ({exc})")
            bad.append((p, ds, mdl, -1))
            continue
        if len(df) != expected_rows:
            bad.append((p, ds, mdl, len(df)))
    return bad


def _backup_and_delete(p: Path, backup_dir: Path, apply: bool) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / p.name
    if apply:
        shutil.copy2(p, dest)
        p.unlink()
        print(f"  moved {p.name}  →  {dest.relative_to(ROOT)}")
    else:
        print(f"  DRY-RUN: would move {p.name}  →  {dest.relative_to(ROOT)}")


def _scrub_checkpoint(bad: List[Tuple[Path, str, str, int]], apply: bool) -> None:
    if not CHECKPOINT.exists():
        print("[repair] no checkpoint file — nothing to scrub.")
        return
    with CHECKPOINT.open() as fh:
        state: Dict[str, bool] = json.load(fh)
    removed = []
    for _, ds, mdl, _ in bad:
        key = f"{ds}__{mdl}"
        if state.pop(key, None) is not None:
            removed.append(key)
    if not removed:
        print("[repair] no matching checkpoint keys to remove.")
        return
    if apply:
        with CHECKPOINT.open("w") as fh:
            json.dump(state, fh, indent=2)
        print(f"[repair] removed {len(removed)} checkpoint keys: {removed}")
    else:
        print(f"[repair] DRY-RUN: would remove keys: {removed}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected_rows", type=int, default=90,
                    help="expected rows per per_query file "
                         "(default 90 = 30 questions × 3 conditions)")
    ap.add_argument("--apply", action="store_true",
                    help="actually delete/backup/scrub (default: dry-run)")
    ap.add_argument("--backup_root", default=None,
                    help="where to stash backups (default: "
                         "results/multidataset/backups_YYYYMMDD/)")
    args = ap.parse_args()

    if not MULTIDATASET_DIR.exists():
        raise SystemExit(f"missing dir: {MULTIDATASET_DIR}")

    bad = _audit(args.expected_rows)
    if not bad:
        print(f"[repair] ✅ all per-query files have {args.expected_rows} rows.")
        return

    print(f"[repair] found {len(bad)} mismatched files "
          f"(expected {args.expected_rows} rows):")
    for p, ds, mdl, n in bad:
        marker = "READ-ERR" if n == -1 else f"{n} rows"
        print(f"    {p.name:<55} ({marker})")

    backup_dir = Path(
        args.backup_root or
        MULTIDATASET_DIR / f"backups_{date.today().isoformat().replace('-', '')}"
    )

    print(f"\n[repair] {'APPLYING' if args.apply else 'DRY-RUN'} — "
          f"backups → {backup_dir}")
    for p, _, _, _ in bad:
        _backup_and_delete(p, backup_dir, args.apply)
    _scrub_checkpoint(bad, args.apply)

    tuples = ",".join(f"{ds}×{mdl}" for _, ds, mdl, _ in bad)
    datasets = sorted({ds for _, ds, _, _ in bad})
    models   = sorted({mdl for _, _, mdl, _ in bad})
    print(f"\n[repair] Re-run these tuples with:\n"
          f"    python3 experiments/run_multidataset_validation.py \\\n"
          f"        --datasets {' '.join(datasets)} \\\n"
          f"        --models {' '.join(models)} \\\n"
          f"        --n_questions {args.expected_rows // 3}\n"
          f"    (checkpoint already cleared for: {tuples})")


if __name__ == "__main__":
    main()
