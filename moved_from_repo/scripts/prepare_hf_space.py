"""
scripts/prepare_hf_space.py — P2 Item 10 finishing touch
=========================================================

Build a self-contained directory ready to `git push` to a HuggingFace Space
repo.  We stage only the files the Space actually needs (the Gradio app,
its requirements, a README with the HF front-matter, and a *slim* subset of
results CSVs + the deployment figure).  That keeps Space cold-start memory
under 4 GB so the free CPU-basic tier is enough.

Usage
-----
    # 1. Build the deploy directory locally:
    python3 scripts/prepare_hf_space.py
    # → writes space_deploy/ with everything in place.

    # 2. Create the Space on HuggingFace (one-time, browser):
    #    https://huggingface.co/new-space
    #    name: coherence-paradox-rag-demo
    #    SDK: Gradio
    #    hardware: CPU basic

    # 3. Push:
    cd space_deploy
    git init
    git lfs install          # for the PNG
    huggingface-cli login    # (uses your HF token)
    git remote add origin git@hf.co:spaces/<your-user>/coherence-paradox-rag-demo
    git add .
    git commit -m "Initial demo push"
    git push -u origin main

    # 4. Space will build automatically (~3 min).  Visit
    #    https://huggingface.co/spaces/<your-user>/coherence-paradox-rag-demo

Notes
-----
* We copy rather than symlink so the `space_deploy/` directory is portable
  if you want to upload via the HF web UI drag-and-drop instead of git.
* `.gitattributes` is written with `*.png filter=lfs` so images use LFS —
  HF Spaces requires LFS for files > 10 MB.
* If you want to redeploy later (new results, updated app), just re-run
  this script and `git push -f` — it overwrites.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_DEST = ROOT / "space_deploy"

# Files the Space *must* have.
CORE_FILES: List[Tuple[str, str]] = [
    ("space/app.py",          "app.py"),
    ("space/requirements.txt","requirements.txt"),
    ("space/README.md",       "README.md"),
]

# Results files the Space displays (paths are ROOT-relative).
RESULT_FILES = [
    "results/multidataset/coherence_paradox.csv",
    "results/headtohead/summary.csv",
    "results/deployment_figure/pareto_summary.csv",
    "results/deployment_figure/latency_vs_faith.png",
]

GITATTRIBUTES = """\
# HF Spaces requires LFS for binary files > 10 MB; keep PNGs in LFS.
*.png filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
"""


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  copied {src.relative_to(ROOT)}  ->  {dst.relative_to(ROOT.parent) if dst.is_relative_to(ROOT.parent) else dst}")


def build(dest: Path, overwrite: bool) -> None:
    if dest.exists():
        if not overwrite:
            raise SystemExit(
                f"{dest} exists — pass --overwrite to rebuild."
            )
        shutil.rmtree(dest)
        print(f"[prep] wiped existing {dest}")

    dest.mkdir(parents=True, exist_ok=True)
    print(f"[prep] staging into {dest}")

    # Core code + docs
    missing: List[str] = []
    for src_rel, dst_rel in CORE_FILES:
        src = ROOT / src_rel
        if not src.exists():
            missing.append(src_rel)
            continue
        _copy(src, dest / dst_rel)

    # Slim results
    for rel in RESULT_FILES:
        src = ROOT / rel
        if not src.exists():
            missing.append(rel)
            continue
        _copy(src, dest / rel)

    if missing:
        print("[prep] WARNING: missing files (Space will still build but "
              "some tabs may show 'missing'):")
        for m in missing:
            print(f"    - {m}")

    # .gitattributes for LFS-tracked binaries
    (dest / ".gitattributes").write_text(GITATTRIBUTES)
    print(f"  wrote {dest / '.gitattributes'}")

    # Tiny push-instructions file inside the dest so you can recall the
    # sequence without re-reading this script.
    push_guide = dest / "_PUSH_INSTRUCTIONS.md"
    push_guide.write_text(
        "# Push to HF Spaces\n"
        "\n"
        "```bash\n"
        "cd space_deploy\n"
        "git init\n"
        "git lfs install\n"
        "huggingface-cli login     # paste your HF token\n"
        "git remote add origin git@hf.co:spaces/<your-user>/coherence-paradox-rag-demo\n"
        "git add .\n"
        "git commit -m 'Initial demo push'\n"
        "git push -u origin main\n"
        "```\n"
        "\n"
        "Auto-build takes ~3 min. Then open\n"
        "`https://huggingface.co/spaces/<your-user>/coherence-paradox-rag-demo`.\n"
    )
    print(f"  wrote {push_guide}")

    print(f"\n[prep] ✅ {dest} is ready to push.")
    print(f"[prep] total files: "
          f"{sum(1 for _ in dest.rglob('*') if _.is_file())}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", default=str(DEFAULT_DEST),
                    help=f"staging directory (default: {DEFAULT_DEST})")
    ap.add_argument("--overwrite", action="store_true",
                    help="wipe and rebuild if dest exists")
    args = ap.parse_args()
    build(Path(args.dest).resolve(), args.overwrite)


if __name__ == "__main__":
    main()
