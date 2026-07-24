"""
scripts/upload_to_zenodo.py — Phase 3 #4
========================================

Upload the ContextCoherenceBench bundle to Zenodo and publish a versioned
DOI. The DOI is what makes the "released benchmark" claim in the paper
defensible to reviewers --- it gives the artifact a permanent,
citation-grade identifier that can be referenced in CITATION.bib.

Two-step flow (Zenodo's standard pattern):
    1. Create a deposition (JSON metadata).
    2. Upload one or more files to that deposition.
    3. Publish (this freezes the version and mints the DOI).

The script supports a sandbox mode that talks to https://sandbox.zenodo.org
so you can rehearse without polluting the production registry.

Prerequisites (one-time):
    1. Free Zenodo account at https://zenodo.org/signup (or sandbox).
    2. Personal access token from
           https://zenodo.org/account/settings/applications/tokens/new/
       Scopes needed: deposit:write, deposit:actions.
    3. Bundle the benchmark dir into a tarball:
           tar -czf release/coherence_bench_v2.tar.gz -C release context_coherence_bench_v1
       (or v2 — pass via --bundle).

Usage:
    export ZENODO_TOKEN=...
    python3 scripts/upload_to_zenodo.py --sandbox            # rehearse
    python3 scripts/upload_to_zenodo.py                      # production

    # With a custom bundle path:
    python3 scripts/upload_to_zenodo.py \\
        --bundle release/coherence_bench_v2.tar.gz \\
        --metadata release/zenodo_metadata.json

The script is idempotent across the steps: if the upload completes but
publishing fails, you can re-invoke with --deposition-id <id> to skip
straight to the publish step.

Returns:
    On success, prints the DOI to stdout. The DOI takes the form
    `10.5281/zenodo.<id>` and resolves at https://doi.org/<DOI>.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_METADATA = ROOT / "release" / "zenodo_metadata.json"
DEFAULT_BUNDLE_DIR = ROOT / "release" / "context_coherence_bench_v1"


def _require(cond: bool, msg: str) -> None:
    if not cond:
        print(f"[zenodo] ❌ {msg}", file=sys.stderr)
        sys.exit(1)


def _api_base(sandbox: bool) -> str:
    return "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"


def _bundle_to_tarball(src_dir: Path, dest: Path) -> Path:
    """If the user passed a directory, tar+gzip it first; if they passed
    an already-built tarball, return it as-is."""
    import tarfile
    if src_dir.is_file():
        return src_dir
    _require(src_dir.is_dir(), f"bundle src is neither dir nor file: {src_dir}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"[zenodo] tarring {src_dir} → {dest}")
    with tarfile.open(dest, "w:gz") as tf:
        tf.add(src_dir, arcname=src_dir.name)
    return dest


def create_deposition(api: str, token: str, metadata: Dict) -> Dict:
    import requests
    r = requests.post(
        f"{api}/deposit/depositions",
        params={"access_token": token},
        json=metadata,
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    _require(r.status_code in (200, 201),
             f"create_deposition failed: HTTP {r.status_code}: {r.text[:300]}")
    body = r.json()
    print(f"[zenodo] created deposition id={body['id']}  draft DOI={body.get('metadata', {}).get('prereserve_doi', {}).get('doi')}")
    return body


def upload_file(api: str, token: str, deposition_id: int, file_path: Path) -> None:
    import requests
    name = file_path.name
    print(f"[zenodo] uploading {name} ({file_path.stat().st_size/1e6:.2f} MB) ...")
    with file_path.open("rb") as fh:
        r = requests.post(
            f"{api}/deposit/depositions/{deposition_id}/files",
            params={"access_token": token},
            data={"name": name},
            files={"file": fh},
            timeout=600,
        )
    _require(r.status_code in (200, 201),
             f"upload_file failed: HTTP {r.status_code}: {r.text[:300]}")
    print(f"[zenodo] ✅ uploaded {name}")


def publish(api: str, token: str, deposition_id: int) -> Dict:
    import requests
    r = requests.post(
        f"{api}/deposit/depositions/{deposition_id}/actions/publish",
        params={"access_token": token},
        timeout=60,
    )
    _require(r.status_code in (200, 202),
             f"publish failed: HTTP {r.status_code}: {r.text[:300]}")
    return r.json()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--metadata", default=str(DEFAULT_METADATA),
                    help=f"path to zenodo metadata json "
                         f"(default: {DEFAULT_METADATA})")
    ap.add_argument("--bundle", default=str(DEFAULT_BUNDLE_DIR),
                    help="bundle to upload — either a directory (will be "
                         "tar+gzipped) or an existing tarball/zip")
    ap.add_argument("--sandbox", action="store_true",
                    help="use sandbox.zenodo.org instead of production")
    ap.add_argument("--deposition-id", type=int, default=None,
                    help="skip create + upload, just publish this id "
                         "(use after a partial upload)")
    ap.add_argument("--no-publish", action="store_true",
                    help="upload but do NOT publish — leaves a draft you "
                         "can preview in the Zenodo web UI before commiting")
    args = ap.parse_args()

    token = os.environ.get("ZENODO_TOKEN", "").strip()
    _require(bool(token), "ZENODO_TOKEN is not set; create one at "
             "https://zenodo.org/account/settings/applications/tokens/new/")
    api = _api_base(args.sandbox)
    print(f"[zenodo] using API base: {api}")

    try:
        import requests  # noqa: F401
    except ImportError:
        _require(False, "pip install requests")

    if args.deposition_id is None:
        meta = json.loads(Path(args.metadata).read_text())
        body = create_deposition(api, token, meta)
        dep_id = body["id"]
        bundle_src = Path(args.bundle)
        tarball = _bundle_to_tarball(
            bundle_src,
            ROOT / "release" / f"{bundle_src.name}.tar.gz",
        )
        upload_file(api, token, dep_id, tarball)
    else:
        dep_id = args.deposition_id
        print(f"[zenodo] resuming with deposition id={dep_id}")

    if args.no_publish:
        print(f"[zenodo] ⏸  not publishing (--no-publish). "
              f"Draft URL: {api.replace('/api','')}/deposit/{dep_id}")
        return
    out = publish(api, token, dep_id)
    doi = (out.get("doi")
           or out.get("metadata", {}).get("doi")
           or out.get("conceptdoi"))
    print()
    print(f"[zenodo] 🎉 published.")
    print(f"[zenodo] DOI:        {doi}")
    print(f"[zenodo] Record URL: https://doi.org/{doi}" if doi else
          f"[zenodo] Record:     {out.get('links', {}).get('html')}")


if __name__ == "__main__":
    main()
