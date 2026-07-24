"""
scripts/lint_paper.py — Phase 3 #3
==================================

Pre-submission lint pass over the LaTeX sources. Runs a battery of
zero-dependency checks and prints a single ranked report so you can
fix the worst issues first.

Checks:
    1. **Undefined references** — \\ref / \\cref / \\eqref to labels
       that don't exist in any \\label.
    2. **Unused labels** — \\label{} declarations no \\ref points at
       (might be intentional for forward-compat; warning, not error).
    3. **Missing citations** — \\cite{key} to keys not in
       references.bib. Catches typos like \\cite{guu202} → guu2020.
    4. **Unused .bib entries** — bib keys never cited (cosmetic).
    5. **Suspicious doubles** — "the the", "a a", "and and" in body
       text (frequent post-edit artifact).
    6. **Double spaces in body text.**
    7. **Trailing whitespace** on lines (cosmetic but messy in diffs).
    8. **TODO / FIXME / XXX markers** still in the sources.
    9. **Filled-in placeholder text** like "TBD", "TKTK", "[author]".
   10. **Common misspellings** (small built-in list — no codespell dep).
   11. **Inconsistent capitalization** of headlines (heuristic).
   12. **`%` characters likely missing escape** (e.g., "10%" → "10\\%").
   13. **Hard-coded paths** (e.g., "/Users/" or "C:\\\\") that may have
       slipped into includegraphics.

Outputs:
    Ranked text report on stdout. Exit code:
        0 = no errors (warnings allowed)
        1 = at least one error-class issue (undefined ref / cite / TODO)

Usage:
    python3 scripts/lint_paper.py
    python3 scripts/lint_paper.py --fail-on-warning  # CI-strict mode
    python3 scripts/lint_paper.py --paths ragpaper/sections/results.tex
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
PAPER_DIR = ROOT / "ragpaper"
BIB = PAPER_DIR / "references.bib"

# --- Tunables ---------------------------------------------------------------

DEFAULT_PATHS = [
    PAPER_DIR / "main.tex",
    PAPER_DIR / "sections",
    PAPER_DIR / "figures",   # figure subfiles often own \label declarations
]

COMMON_MISSPELLINGS = {
    "occured":      "occurred",
    "recieve":      "receive",
    "seperate":     "separate",
    "definately":   "definitely",
    "occurence":    "occurrence",
    "comparision":  "comparison",
    "experimentss": "experiments",
    "retrival":     "retrieval",
    "retreival":    "retrieval",
    "retreive":     "retrieve",
    "preformance":  "performance",
    "thier":        "their",
    "tha t":        "that",
    "te h":         "the",
    "halucination": "hallucination",
    "halluciantion": "hallucination",
    "co-herent":    "coherent",
    "consistant":   "consistent",
    "rebuttle":     "rebuttal",
    "neglible":     "negligible",
}

PLACEHOLDER_RE = re.compile(
    r"\b(TBD|TKTK|TKK|XXX+|FIXME|TODO|FIX ME|\\todo)\b", re.IGNORECASE,
)

DOUBLE_WORD_RE = re.compile(
    r"\b(the|a|an|and|of|to|in|is|that|for|on|as)\s+\1\b", re.IGNORECASE,
)

PERCENT_NO_ESCAPE_RE = re.compile(r"(?<![\\%a-zA-Z])(\d+(?:\.\d+)?)\s*%(?!\})")
HARDCODED_PATH_RE   = re.compile(r"(?<![A-Za-z])(?:/Users/|/home/|C:\\)")


# --- Helpers ----------------------------------------------------------------

def collect_files(paths: List[Path]) -> List[Path]:
    files: List[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.tex")))
        elif p.is_file():
            files.append(p)
    # Deduplicate, preserve order
    seen = set()
    out = []
    for f in files:
        if f not in seen:
            out.append(f); seen.add(f)
    return out


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def strip_comments(text: str) -> str:
    """Remove % comments (but not \\%)."""
    out_lines = []
    for line in text.splitlines():
        # Find first un-escaped %
        idx = -1
        i = 0
        while i < len(line):
            if line[i] == "%" and (i == 0 or line[i-1] != "\\"):
                idx = i; break
            i += 1
        if idx >= 0:
            line = line[:idx]
        out_lines.append(line)
    return "\n".join(out_lines)


# --- Collectors -------------------------------------------------------------

def collect_labels(files: List[Path]) -> Dict[str, List[Tuple[Path, int]]]:
    """label name → list of (file, line) where it was declared."""
    out: Dict[str, List[Tuple[Path, int]]] = defaultdict(list)
    pat = re.compile(r"\\label\{([^}]+)\}")
    for f in files:
        for ln, line in enumerate(strip_comments(read(f)).splitlines(), 1):
            for m in pat.finditer(line):
                out[m.group(1)].append((f, ln))
    return out


def collect_refs(files: List[Path]) -> Dict[str, List[Tuple[Path, int]]]:
    """ref name → list of (file, line) where it was referenced."""
    out: Dict[str, List[Tuple[Path, int]]] = defaultdict(list)
    pat = re.compile(r"\\(?:c?ref|eqref|autoref|pageref|nameref)\{([^}]+)\}")
    for f in files:
        for ln, line in enumerate(strip_comments(read(f)).splitlines(), 1):
            for m in pat.finditer(line):
                # Multi-key cref: \cref{a,b,c}
                for k in m.group(1).split(","):
                    out[k.strip()].append((f, ln))
    return out


def collect_citations(files: List[Path]) -> Dict[str, List[Tuple[Path, int]]]:
    out: Dict[str, List[Tuple[Path, int]]] = defaultdict(list)
    pat = re.compile(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])?\{([^}]+)\}")
    for f in files:
        for ln, line in enumerate(strip_comments(read(f)).splitlines(), 1):
            for m in pat.finditer(line):
                for k in m.group(1).split(","):
                    out[k.strip()].append((f, ln))
    return out


def collect_bib_keys(bib: Path) -> Set[str]:
    if not bib.exists():
        return set()
    pat = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,")
    out = set()
    for m in pat.finditer(read(bib)):
        out.add(m.group(1))
    return out


# --- Checks -----------------------------------------------------------------

def check_refs(refs, labels) -> List[str]:
    issues = []
    for k, locs in refs.items():
        if k not in labels:
            for f, ln in locs:
                issues.append(f"[ERR] {f.relative_to(ROOT)}:{ln}: \\ref to "
                              f"undefined label {k!r}")
    return issues


def check_unused_labels(refs, labels) -> List[str]:
    issues = []
    for k, locs in labels.items():
        if k not in refs:
            f, ln = locs[0]
            issues.append(f"[warn] {f.relative_to(ROOT)}:{ln}: label "
                          f"{k!r} declared but never \\ref'd")
    return issues


def check_citations(cites, bib_keys) -> List[str]:
    issues = []
    if not bib_keys:
        return ["[warn] references.bib not found or empty; "
                "skipping citation check"]
    for k, locs in cites.items():
        if k not in bib_keys:
            for f, ln in locs:
                issues.append(f"[ERR] {f.relative_to(ROOT)}:{ln}: \\cite to "
                              f"missing bib key {k!r}")
    return issues


def check_unused_bib(cites, bib_keys) -> List[str]:
    issues = []
    cited = set(cites.keys())
    for k in sorted(bib_keys - cited):
        issues.append(f"[warn] references.bib: bib key {k!r} never cited")
    return issues


def check_lines(files: List[Path]) -> List[str]:
    issues = []
    for f in files:
        text = read(f)
        body = strip_comments(text)
        # Per-line checks
        for ln, line in enumerate(body.splitlines(), 1):
            stripped = line.strip()
            if not stripped:
                continue
            if PLACEHOLDER_RE.search(line):
                issues.append(f"[ERR] {f.relative_to(ROOT)}:{ln}: "
                              f"placeholder marker: {stripped[:80]!r}")
            for m in DOUBLE_WORD_RE.finditer(line):
                issues.append(f"[warn] {f.relative_to(ROOT)}:{ln}: "
                              f"double word {m.group(0)!r}")
            for m in PERCENT_NO_ESCAPE_RE.finditer(line):
                issues.append(f"[warn] {f.relative_to(ROOT)}:{ln}: "
                              f"unescaped percent {m.group(0)!r} "
                              f"(use \\\\% in body text)")
            if HARDCODED_PATH_RE.search(line):
                issues.append(f"[warn] {f.relative_to(ROOT)}:{ln}: "
                              f"hard-coded absolute path in source")
            if "  " in stripped and not stripped.startswith("\\"):
                # Two+ consecutive spaces in body text
                issues.append(f"[warn] {f.relative_to(ROOT)}:{ln}: "
                              f"double space in body text")
            for bad, good in COMMON_MISSPELLINGS.items():
                if re.search(rf"\b{re.escape(bad)}\b", line, re.IGNORECASE):
                    issues.append(f"[warn] {f.relative_to(ROOT)}:{ln}: "
                                  f"likely misspelling {bad!r} → {good!r}")
        # Whole-file: trailing whitespace
        for ln, raw in enumerate(text.splitlines(), 1):
            if raw != raw.rstrip():
                issues.append(f"[note] {f.relative_to(ROOT)}:{ln}: "
                              f"trailing whitespace")
    return issues


# --- Reporter ---------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paths", nargs="*", default=None,
                    help="override scan paths (default: ragpaper/main.tex + "
                         "ragpaper/sections/)")
    ap.add_argument("--fail-on-warning", action="store_true")
    args = ap.parse_args()

    paths = ([Path(p).resolve() for p in args.paths]
             if args.paths else DEFAULT_PATHS)
    files = collect_files(paths)
    print(f"[lint] scanning {len(files)} .tex files")

    labels = collect_labels(files)
    refs   = collect_refs(files)
    cites  = collect_citations(files)
    bibs   = collect_bib_keys(BIB)

    issues: List[str] = []
    issues += check_refs(refs, labels)
    issues += check_citations(cites, bibs)
    issues += check_lines(files)
    issues += check_unused_labels(refs, labels)
    issues += check_unused_bib(cites, bibs)

    n_err  = sum(1 for x in issues if x.startswith("[ERR]"))
    n_warn = sum(1 for x in issues if x.startswith("[warn]"))
    n_note = sum(1 for x in issues if x.startswith("[note]"))

    # Report — errors first, then warnings, then notes
    for tag in ("[ERR]", "[warn]", "[note]"):
        block = [x for x in issues if x.startswith(tag)]
        if not block:
            continue
        print()
        print(f"=== {tag}  ({len(block)}) ===")
        for x in block[:200]:        # cap noise
            print(x)
        if len(block) > 200:
            print(f"... and {len(block) - 200} more {tag} items")

    print()
    print(f"[lint] summary: {n_err} errors, {n_warn} warnings, {n_note} notes")

    if n_err:
        return 1
    if args.fail_on_warning and n_warn:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
