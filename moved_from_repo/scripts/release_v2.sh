#!/usr/bin/env bash
# scripts/release_v2.sh — Path 3 finishing touch
# ===============================================
# Tag and push the NeurIPS-submission release.  Bundles results, paper PDF,
# and a release-notes blob into a `v2.0.0` GitHub release.
#
# What this script does
# ---------------------
#   1. Verifies working tree is clean (no uncommitted code changes that
#      should have been committed before tagging).
#   2. Builds a slim release artifact tarball at /tmp/coherence-paradox-v2.tar.gz
#      containing: paper PDF, slim results CSVs, leaderboard config, demo
#      Space staged dir.  Excludes raw chroma DBs and per-run logs.
#   3. Creates an annotated git tag `v2.0.0` (or whatever --tag is passed).
#   4. Pushes the tag to origin.
#   5. (Optional, if `gh` CLI is present and authenticated) creates the
#      GitHub Release and uploads the tarball as an asset.
#
# Usage
# -----
#   bash scripts/release_v2.sh                 # tag v2.0.0
#   bash scripts/release_v2.sh --tag v2.1.0    # custom tag
#   bash scripts/release_v2.sh --dry-run       # show what would happen
#
# Environment
# -----------
#   GH_TOKEN  — optional, picked up by the `gh` CLI if you have it.
#
# Safety
# ------
# This script ONLY adds a tag and (optionally) a Release.  It never force-
# pushes branches or rewrites history.

set -euo pipefail

TAG="v2.0.0"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)      TAG="$2"; shift 2 ;;
    --dry-run)  DRY_RUN=1; shift ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "[release] unknown arg: $1"; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[release] repo root: $ROOT"
echo "[release] tag:       $TAG"
echo "[release] dry-run:   $DRY_RUN"
echo

# ── 1. Tree must be clean (ignore binary chroma + cache noise) ──────────
DIRTY=$(git status --porcelain | grep -vE '(\.DS_Store|chroma_db/|__pycache__/|\.pyc$|ragpaper\.zip$)' || true)
if [[ -n "$DIRTY" ]]; then
  echo "[release] ❌ uncommitted changes (excluding caches):"
  echo "$DIRTY"
  echo "[release] commit or stash before tagging."
  exit 1
fi
echo "[release] ✅ working tree clean (caches ignored)"

# ── 2. Sanity: required artifacts exist ─────────────────────────────────
REQUIRED=(
  "ragpaper/main.tex"
  "results/multidataset/summary.csv"
  "results/headtohead/summary.csv"
  "results/multiseed"
  "results/raptor"
  "results/longform"
  "results/noise_injection"
  "results/prompt_ablation"
  "results/subchunk_sensitivity"
  "results/frontier_scale/paradox_by_scale.csv"
  "space/app.py"
  "leaderboard/app.py"
)
MISSING=()
for f in "${REQUIRED[@]}"; do
  [[ -e "$f" ]] || MISSING+=("$f")
done
if (( ${#MISSING[@]} > 0 )); then
  echo "[release] ❌ missing required artifacts:"
  printf '   - %s\n' "${MISSING[@]}"
  exit 1
fi
echo "[release] ✅ release artifacts present"

# ── 3. Build the release tarball ────────────────────────────────────────
ARTIFACT="/tmp/coherence-paradox-${TAG}.tar.gz"
echo "[release] building $ARTIFACT"
if (( DRY_RUN == 0 )); then
  tar --exclude='chroma_db' \
      --exclude='chroma_db_*' \
      --exclude='__pycache__' \
      --exclude='*.pyc' \
      --exclude='.DS_Store' \
      --exclude='ragpaper/build' \
      --exclude='ragpaper/main.aux' \
      --exclude='ragpaper/main.log' \
      -czf "$ARTIFACT" \
      ragpaper/main.tex ragpaper/main.pdf ragpaper/sections ragpaper/figures ragpaper/references.bib \
      results/multidataset/summary.csv \
      results/multidataset/coherence_paradox.csv \
      results/headtohead/summary.csv \
      results/multiseed \
      results/raptor \
      results/longform \
      results/noise_injection \
      results/prompt_ablation \
      results/subchunk_sensitivity \
      results/frontier_scale \
      results/deployment_figure \
      space leaderboard scripts experiments src README.md \
      2>/dev/null || true
  ls -lh "$ARTIFACT"
else
  echo "[release] (dry-run) would tar to $ARTIFACT"
fi

# ── 4. Tag ──────────────────────────────────────────────────────────────
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "[release] ⚠️  tag $TAG already exists; skipping creation."
else
  MSG="Coherence Paradox in RAG — $TAG

NeurIPS 2026 submission release.

Headlines:
  - Refinement paradox documented across SQuAD/PubMedQA, Mistral-7B/Llama-3-8B
  - HCPC-v2 selective refinement recovers faithfulness with 0% hallucination
  - Context Coherence Score (CCS) as retrieval-time diagnostic
  - 6 robustness checks (multi-seed, RAPTOR, prompt, sub-chunk, long-form, noise)

Artifacts:
  - ragpaper/        — full LaTeX + compiled PDF
  - results/         — per-query and aggregated metrics
  - space/           — Gradio demo
  - leaderboard/     — submission portal
  - scripts/         — Path 2 Groq frontier-scale + Path 3 HF-Space staging
"
  if (( DRY_RUN == 0 )); then
    git tag -a "$TAG" -m "$MSG"
    echo "[release] ✅ tagged $TAG"
  else
    echo "[release] (dry-run) would tag $TAG with annotated message"
  fi
fi

# ── 5. Push tag ─────────────────────────────────────────────────────────
if (( DRY_RUN == 0 )); then
  git push origin "$TAG"
  echo "[release] ✅ pushed tag to origin"
else
  echo "[release] (dry-run) would push $TAG to origin"
fi

# ── 6. GitHub Release (optional, requires `gh`) ─────────────────────────
if command -v gh >/dev/null 2>&1; then
  if (( DRY_RUN == 0 )); then
    if gh release view "$TAG" >/dev/null 2>&1; then
      echo "[release] ⚠️  GitHub Release $TAG already exists; uploading asset."
      gh release upload "$TAG" "$ARTIFACT" --clobber
    else
      gh release create "$TAG" "$ARTIFACT" \
        --title "Coherence Paradox in RAG — $TAG" \
        --notes "See the packaged manifest for full details. \
Tarball includes: paper LaTeX, slim results CSVs, Gradio demo, leaderboard, \
and Path 2/3 staging scripts."
    fi
    echo "[release] ✅ GitHub Release ready"
  else
    echo "[release] (dry-run) would create gh release $TAG with $ARTIFACT"
  fi
else
  echo "[release] (no gh CLI; skipped GitHub Release step — tag was pushed)"
  echo "[release]    Manually create the release at:"
  REMOTE=$(git config --get remote.origin.url | sed -E 's#git@github.com:#https://github.com/#; s#\.git$##')
  echo "[release]    ${REMOTE}/releases/new?tag=${TAG}"
fi

echo
echo "[release] 🎉 done."
