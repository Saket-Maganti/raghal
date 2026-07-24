
"""Build a deterministic output ZIP and checksum manifest."""
from __future__ import annotations
import argparse
import hashlib
import zipfile
from pathlib import Path

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def package(output_root: str | Path, zip_path: str | Path) -> dict:
    root, destination = Path(output_root), Path(zip_path)
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")
    checksums = "\n".join(f"{sha(p)}  {p.relative_to(root).as_posix()}" for p in files) + "\n"
    (root / "SHA256SUMS.txt").write_text(checksums)
    files.append(root / "SHA256SUMS.txt")
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            info = zipfile.ZipInfo(
                f"CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT/{path.relative_to(root).as_posix()}",
                date_time=(1980, 1, 1, 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return {"files": len(files), "zip_sha256": sha(destination), "zip_bytes": destination.stat().st_size}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root")
    parser.add_argument("zip_path")
    args = parser.parse_args()
    print(package(args.output_root, args.zip_path))

if __name__ == "__main__":
    main()
