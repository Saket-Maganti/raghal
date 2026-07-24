#!/usr/bin/env python3
"""Build a deterministic, publication-aware forensic snapshot of four source trees.

This script reads the source trees but writes only to the separate ingest clone.
It intentionally does not execute project code or alter nested Git repositories.
"""

from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
import stat
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


SOURCE_ROOT = Path(os.environ.get("RAGHAL_SOURCE_ROOT", "/path/to/raghallucination"))
REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = REPO_ROOT / "audit"
LOCAL_WORKSPACE = REPO_ROOT.parent
SOURCE_FOLDERS = [
    "cleanup_20260506_final_code_artifact_cleanup",
    "deleted_from_head",
    "moved_from_repo",
    "rag-hallucination-detection_main",
]
SUBMITTED_FOLDER = "rag-hallucination-detection_main"
GITHUB_HARD_LIMIT = 100 * 1024 * 1024
LARGE_REVIEW_LIMIT = 50 * 1024 * 1024

CACHE_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".ipynb_checkpoints",
}
OS_METADATA = {".DS_Store", "Thumbs.db"}
PRIVATE_KEY_SUFFIXES = {".pem", ".p12", ".pfx", ".jks"}
ARCHIVE_SUFFIXES = {".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z"}
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".sqlite", ".sqlite3",
    ".db", ".parquet", ".pkl", ".pickle", ".npy", ".npz", ".pt", ".pth",
    ".bin", ".woff", ".woff2", ".ttf", ".ico", ".pack", ".idx",
} | ARCHIVE_SUFFIXES

SECRET_PATTERNS = [
    ("github_token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("personal_email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("personal_identity", re.compile(r"(?i)\b(?:Saket[\s-]+Maganti|Saket-Maganti|saketmgnt|freeopenapex)\b")),
    (
        "assigned_secret",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|client[_-]?secret)"
            r"\s*[:=]\s*[\"']([^\"'\r\n]{8,})[\"']"
        ),
    ),
]
PLACEHOLDER_FRAGMENTS = {
    "placeholder", "example", "your_", "your-", "replace", "dummy", "test",
    "xxxx", "<", "${", "os.environ", "getenv", "none", "null", "changeme",
}
PROMPT_INJECTION_TERMS = [
    "ignore previous instructions",
    "ignore all previous",
    "system prompt",
    "developer message",
    "prompt injection",
    "disregard previous",
]
CONFIDENTIAL_NAME_TERMS = [
    "openreview_private",
    "reviewer_screenshot",
    "peer_review_screenshot",
    "confidential_review",
    "private_review",
    "reviewer_identity",
    "email_export",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def redact_email(value: str) -> str:
    if not value or "@" not in value:
        return value
    if value.endswith("@users.noreply.github.com"):
        return value
    return "<redacted-email>"


def redact_url(value: str) -> str:
    value = re.sub(r"(https?://)[^/@\s]+@", r"\1<redacted>@", value)
    value = re.sub(r"(?i)(token|key|password|passwd|secret)=([^&\s]+)", r"\1=<redacted>", value)
    return value


def read_text_for_scan(path: Path, max_bytes: int = 20 * 1024 * 1024) -> str | None:
    try:
        if path.stat().st_size > max_bytes or path.suffix.lower() in BINARY_SUFFIXES:
            return None
        raw = path.read_bytes()
        if b"\x00" in raw[:8192]:
            return None
        return raw.decode("utf-8", errors="replace")
    except OSError:
        return None


def scan_text(text: str) -> tuple[list[str], list[str], list[str]]:
    secrets: list[str] = []
    for label, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            candidate = match.group(1) if match.lastindex else match.group(0)
            lowered = candidate.lower()
            if label == "personal_email" and (
                lowered.startswith("git@")
                or lowered.endswith("@users.noreply.github.com")
                or "replace_with" in lowered
                or not any(identifier in lowered for identifier in ("saket", "freeopenapex"))
            ):
                continue
            if label == "assigned_secret" and any(piece in lowered for piece in PLACEHOLDER_FRAGMENTS):
                continue
            secrets.append(label)
            break
    lowered_text = text.lower()
    injections = [term for term in PROMPT_INJECTION_TERMS if term in lowered_text]
    home_paths = sorted(set(re.findall(r"/Users/[A-Za-z0-9._-]+/[^\s\"'`,;)}\]]*", text)))
    return sorted(set(secrets)), sorted(set(injections)), home_paths[:20]


def scan_archive(path: Path) -> tuple[list[str], list[str]]:
    if path.suffix.lower() != ".zip":
        return [], []
    secret_hits: set[str] = set()
    suspicious_members: set[str] = set()
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                member_lower = info.filename.lower()
                if any(term in member_lower for term in CONFIDENTIAL_NAME_TERMS):
                    suspicious_members.add(info.filename)
                if info.file_size > 2 * 1024 * 1024 or info.is_dir():
                    continue
                suffix = Path(info.filename).suffix.lower()
                if suffix in BINARY_SUFFIXES:
                    continue
                try:
                    text = archive.read(info).decode("utf-8", errors="replace")
                except (OSError, RuntimeError, zipfile.BadZipFile):
                    continue
                found, _, _ = scan_text(text)
                secret_hits.update(f"{label}:archive-member:{info.filename}" for label in found)
    except (OSError, zipfile.BadZipFile):
        suspicious_members.add("<archive-unreadable>")
    return sorted(secret_hits), sorted(suspicious_members)


def scan_pdf(path: Path) -> tuple[list[str], list[str], list[str]]:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        return [], [], []
    try:
        result = subprocess.run(
            [pdftotext, str(path), "-"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return [], [], []
    if result.returncode != 0:
        return [], [], []
    return scan_text(result.stdout)


def classify_asset(relative_path: Path) -> str:
    lower = relative_path.as_posix().lower()
    suffix = relative_path.suffix.lower()
    if any(part in CACHE_PARTS for part in relative_path.parts) or "chroma_db" in lower:
        return "cache"
    if suffix in {".py", ".sh", ".r", ".jl", ".java", ".js", ".ts"}:
        return "source"
    if suffix == ".ipynb":
        return "notebook"
    if suffix in {".csv", ".tsv", ".jsonl", ".parquet", ".arrow"}:
        if any(term in lower for term in ("result", "metric", "score", "evaluation", "eval", "figure", "table")):
            return "result"
        return "data"
    if suffix in {".tex", ".bib", ".sty", ".cls"} or "paper" in lower:
        return "paper"
    if suffix in {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".eps"}:
        return "figure" if "figure" in lower else "paper" if suffix == ".pdf" else "result"
    if suffix in {".log", ".out"} or "logs" in relative_path.parts:
        return "log"
    if relative_path.name.lower().startswith(("requirements", "environment", "pyproject", "setup", "dockerfile")):
        return "environment"
    if suffix in {".pt", ".pth", ".safetensors", ".ckpt", ".bin"}:
        return "model"
    if suffix in ARCHIVE_SUFFIXES:
        return "archive"
    if relative_path.name.lower().startswith(("license", "readme")) or suffix in {".md", ".txt", ".yaml", ".yml", ".toml"}:
        return "source"
    return "unknown"


def determine_action(
    source_folder: str,
    relative_path: Path,
    size: int,
    secrets: list[str],
    archive_suspicion: list[str],
    home_paths: list[str],
) -> tuple[bool, str, str]:
    parts = set(relative_path.parts)
    lower = relative_path.as_posix().lower()
    name_lower = relative_path.name.lower()
    if ".git" in parts:
        return False, "exclude", "nested Git metadata; textual provenance exported separately"
    relative_string = relative_path.as_posix()
    if source_folder == "deleted_from_head" and (
        relative_string in {
            "AGENTS.md",
            "CLAUDE.md",
            "RUNBOOK.md",
            "OPENREVIEW_ABSTRACT_READY.md",
            "SUBMIT_READY.md",
            "SUBMISSION_CHECKLIST.md",
            "SUBMISSION_READINESS_CHECKLIST.md",
        }
        or relative_string.startswith("docs/revision/")
        or relative_string.startswith("submission/")
    ):
        return False, "exclude", "internal assistant/revision or private submission material"
    if (
        source_folder == "moved_from_repo"
        and relative_string == "human_eval_final/scripts/complete_human_eval.py"
    ):
        return False, "exclude", "personal adjudication authoring material"
    if any(part in CACHE_PARTS for part in relative_path.parts):
        return False, "exclude", "generated cache or local environment"
    if relative_path.name in OS_METADATA:
        return False, "exclude", "operating-system metadata"
    if name_lower == ".env" or name_lower.startswith(".env."):
        return False, "exclude", "environment file requires secret review"
    if relative_path.suffix.lower() in PRIVATE_KEY_SUFFIXES or name_lower in {"id_rsa", "id_ed25519"}:
        return False, "exclude", "credential or private-key material"
    if home_paths:
        return False, "exclude", "absolute home path contains a personal identifier"
    if secrets:
        if set(secrets).issubset({"personal_email", "personal_identity"}):
            return False, "exclude", "personal author identity in publication copy"
        return False, "exclude", f"high-confidence secret or personal-data pattern: {', '.join(secrets)}"
    if any(term in lower for term in CONFIDENTIAL_NAME_TERMS) or archive_suspicion:
        detail = ", ".join(archive_suspicion[:3]) if archive_suspicion else "confidential filename pattern"
        return False, "exclude", f"potential confidential/private material: {detail}"
    if "chroma_db" in lower or relative_path.suffix.lower() in {".sqlite", ".sqlite3"}:
        return False, "exclude", "generated vector/database cache; reconstruct rather than publish"
    if size >= GITHUB_HARD_LIMIT:
        return False, "exclude", "exceeds GitHub 100 MiB hard limit"
    if size >= LARGE_REVIEW_LIMIT:
        return False, "manual review", "large generated/external asset; omitted pending explicit review"
    return True, "include", "publication-safe under automated gate"


def csv_write(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def markdown_list(paths: list[str], limit: int = 40) -> str:
    if not paths:
        return "- None found."
    rendered = [f"- `{path}`" for path in paths[:limit]]
    if len(paths) > limit:
        rendered.append(f"- … {len(paths) - limit} additional paths are listed in the CSV manifests.")
    return "\n".join(rendered)


def safe_unlink_tree_contents(destination: Path) -> None:
    if not destination.exists():
        return
    for child in destination.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def git_provenance() -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    state_sections: list[str] = []
    commit_rows: list[dict[str, str]] = []
    remote_rows: list[dict[str, str]] = []
    nested_repos: list[str] = []
    for folder in SOURCE_FOLDERS:
        path = SOURCE_ROOT / folder
        git_dir = path / ".git"
        state_sections.append(f"## `{folder}`")
        if not git_dir.exists():
            state_sections.append("\nType: plain directory; no nested `.git` root detected.\n")
            continue
        nested_repos.append(folder)
        commands = {
            "Repository root": ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            "Branch": ["git", "-C", str(path), "branch", "--show-current"],
            "HEAD": ["git", "-C", str(path), "rev-parse", "HEAD"],
            "Status": ["git", "-C", str(path), "status", "--short", "--branch"],
            "Tags": ["git", "-C", str(path), "tag", "--list"],
            "Submodules": ["git", "-C", str(path), "submodule", "status"],
            "Shallow": ["git", "-C", str(path), "rev-parse", "--is-shallow-repository"],
            "LFS files": ["git", "-C", str(path), "lfs", "ls-files"],
        }
        for label, command in commands.items():
            code, stdout, stderr = run(command)
            value = stdout or ("None" if code == 0 else f"Unavailable: {stderr}")
            if label == "Repository root":
                value = f"/Users/<redacted>/Projects/raghallucination/{folder}"
            state_sections.append(f"\n**{label}**\n\n```text\n{value}\n```\n")
        code, ignored, _ = run(["git", "-C", str(path), "status", "--ignored", "--short"])
        ignored_count = sum(1 for line in ignored.splitlines() if line.startswith("!!")) if code == 0 else 0
        state_sections.append(f"\nIgnored path entries reported: {ignored_count}.\n")
        code, log_output, _ = run(
            [
                "git", "-C", str(path), "log", "-30",
                "--pretty=format:%H%x1f%an%x1f%ae%x1f%aI%x1f%cI%x1f%s",
            ]
        )
        if code == 0:
            for line in log_output.splitlines():
                parts = line.split("\x1f")
                if len(parts) == 6:
                    commit_rows.append(
                        {
                            "source_folder": folder,
                            "commit_sha": parts[0],
                            "author_name": parts[1],
                            "author_email": redact_email(parts[2]),
                            "author_date": parts[3],
                            "commit_date": parts[4],
                            "subject": parts[5],
                        }
                    )
        code, remotes, _ = run(["git", "-C", str(path), "remote", "-v"])
        if code == 0:
            for line in remotes.splitlines():
                fields = line.split()
                if len(fields) >= 3:
                    remote_rows.append(
                        {
                            "source_folder": folder,
                            "remote": fields[0],
                            "url_redacted": redact_url(fields[1]),
                            "direction": fields[2].strip("()"),
                        }
                    )
    state = [
        "# Nested Git State",
        "",
        "Generated from the source trees without modifying them. Personal home-directory components and non-GitHub author emails are redacted in this publication copy.",
        "",
        *state_sections,
    ]
    (AUDIT_DIR / "NESTED_GIT_STATE.md").write_text("\n".join(state), encoding="utf-8")
    csv_write(
        AUDIT_DIR / "NESTED_GIT_COMMITS.csv",
        ["source_folder", "commit_sha", "author_name", "author_email", "author_date", "commit_date", "subject"],
        commit_rows,
    )
    remote_lines = [
        "# Nested Git Remotes (Redacted)",
        "",
        "Credentials and URL query secrets are redacted. No nested `.git` directory is included in the snapshot.",
        "",
    ]
    for row in remote_rows:
        remote_lines.append(
            f"- `{row['source_folder']}` — `{row['remote']}` ({row['direction']}): `{row['url_redacted']}`"
        )
    if not remote_rows:
        remote_lines.append("- No remotes detected.")
    (AUDIT_DIR / "NESTED_GIT_REMOTES_REDACTED.md").write_text("\n".join(remote_lines) + "\n", encoding="utf-8")
    return commit_rows, remote_rows, nested_repos


def build_inventory_and_copy() -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, list[str]]]:
    records: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    scan_findings: dict[str, list[str]] = defaultdict(list)
    for folder in SOURCE_FOLDERS:
        source = SOURCE_ROOT / folder
        destination = REPO_ROOT / folder
        destination.mkdir(parents=True, exist_ok=True)
        for path in sorted(source.rglob("*"), key=lambda item: item.relative_to(source).as_posix()):
            relative = path.relative_to(source)
            try:
                file_stat = path.lstat()
            except OSError as exc:
                scan_findings["unreadable"].append(f"{folder}/{relative}: {exc}")
                continue
            if stat.S_ISDIR(file_stat.st_mode):
                if ".git" not in relative.parts:
                    (destination / relative).mkdir(parents=True, exist_ok=True)
                continue
            if stat.S_ISLNK(file_stat.st_mode):
                target = os.readlink(path)
                digest = hashlib.sha256(target.encode()).hexdigest()
                records.append(
                    {
                        "source_folder": folder,
                        "relative_path": relative.as_posix(),
                        "size_bytes": len(target.encode()),
                        "modified_timestamp": datetime.fromtimestamp(file_stat.st_mtime).astimezone().isoformat(),
                        "extension_or_type": "symlink",
                        "sha256": digest,
                        "text_or_binary": "symlink",
                        "asset_class": "unknown",
                        "safe_to_publish": "no",
                        "proposed_action": "manual review",
                        "action_reason": f"symlink target not copied: {target}",
                        "secret_findings": "",
                        "prompt_injection_terms": "",
                        "home_paths_found": "",
                    }
                )
                excluded.append(
                    {
                        "source_folder": folder,
                        "relative_path": relative.as_posix(),
                        "size_bytes": len(target.encode()),
                        "sha256": digest,
                        "exclusion_reason": f"symlink requires manual review; target={target}",
                    }
                )
                continue
            if not stat.S_ISREG(file_stat.st_mode):
                continue
            digest = sha256_file(path)
            text = read_text_for_scan(path)
            secret_hits: list[str] = []
            injection_hits: list[str] = []
            home_paths: list[str] = []
            if text is not None:
                secret_hits, injection_hits, home_paths = scan_text(text)
            elif path.suffix.lower() == ".pdf":
                pdf_secrets, pdf_injections, pdf_home_paths = scan_pdf(path)
                secret_hits.extend(pdf_secrets)
                injection_hits.extend(pdf_injections)
                home_paths.extend(pdf_home_paths)
            archive_secret_hits, archive_suspicion = scan_archive(path)
            secret_hits.extend(archive_secret_hits)
            include, action, reason = determine_action(
                folder,
                relative,
                file_stat.st_size,
                sorted(set(secret_hits)),
                archive_suspicion,
                home_paths,
            )
            asset_class = classify_asset(relative)
            mime, _ = mimetypes.guess_type(path.name)
            extension_type = path.suffix.lower() or mime or "no-extension"
            record = {
                "source_folder": folder,
                "relative_path": relative.as_posix(),
                "size_bytes": file_stat.st_size,
                "modified_timestamp": datetime.fromtimestamp(file_stat.st_mtime).astimezone().isoformat(),
                "extension_or_type": extension_type,
                "sha256": digest,
                "text_or_binary": "text" if text is not None else "binary",
                "asset_class": asset_class,
                "safe_to_publish": "yes" if include else "no",
                "proposed_action": action,
                "action_reason": reason,
                "secret_findings": ";".join(sorted(set(secret_hits))),
                "prompt_injection_terms": ";".join(injection_hits),
                "home_paths_found": str(len(home_paths)),
            }
            records.append(record)
            source_key = f"{folder}/{relative.as_posix()}"
            if injection_hits:
                scan_findings["prompt_injection"].append(f"{source_key}: {', '.join(injection_hits)}")
            if home_paths:
                scan_findings["home_paths"].append(f"{source_key}: {len(home_paths)} path(s)")
            if secret_hits:
                scan_findings["secrets"].append(f"{source_key}: {', '.join(sorted(set(secret_hits)))}")
            if archive_suspicion:
                scan_findings["archive_suspicion"].append(f"{source_key}: {', '.join(archive_suspicion)}")
            if include:
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            else:
                excluded.append(
                    {
                        "source_folder": folder,
                        "relative_path": relative.as_posix(),
                        "size_bytes": file_stat.st_size,
                        "sha256": digest,
                        "exclusion_reason": reason,
                    }
                )
    return records, excluded, scan_findings


def write_inventory_reports(records: list[dict[str, object]], excluded: list[dict[str, object]]) -> None:
    manifest_fields = [
        "source_folder", "relative_path", "size_bytes", "modified_timestamp",
        "extension_or_type", "sha256", "text_or_binary", "asset_class",
        "safe_to_publish", "proposed_action", "action_reason", "secret_findings",
        "prompt_injection_terms", "home_paths_found",
    ]
    csv_write(AUDIT_DIR / "ALL_FILES_MANIFEST.csv", manifest_fields, records)
    csv_write(
        AUDIT_DIR / "PUBLICATION_SAFETY_CLASSIFICATION.csv",
        [
            "source_folder", "relative_path", "size_bytes", "sha256",
            "safe_to_publish", "proposed_action", "action_reason", "secret_findings",
        ],
        records,
    )
    largest = sorted(records, key=lambda row: int(row["size_bytes"]), reverse=True)
    csv_write(
        AUDIT_DIR / "LARGEST_FILES.csv",
        ["source_folder", "relative_path", "size_bytes", "sha256", "asset_class", "proposed_action", "action_reason"],
        largest,
    )
    type_counts: Counter[tuple[str, str, str]] = Counter()
    for row in records:
        type_counts[(str(row["source_folder"]), str(row["extension_or_type"]), str(row["asset_class"]))] += 1
    type_rows = [
        {"source_folder": folder, "extension_or_type": extension, "asset_class": asset_class, "file_count": count}
        for (folder, extension, asset_class), count in sorted(type_counts.items())
    ]
    csv_write(
        AUDIT_DIR / "FILE_TYPE_SUMMARY.csv",
        ["source_folder", "extension_or_type", "asset_class", "file_count"],
        type_rows,
    )
    csv_write(
        AUDIT_DIR / "EXCLUDED_FILES_MANIFEST.csv",
        ["source_folder", "relative_path", "size_bytes", "sha256", "exclusion_reason"],
        excluded,
    )
    large_external = [
        {
            "source_folder": row["source_folder"],
            "relative_path": row["relative_path"],
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
            "asset_class": row["asset_class"],
            "proposed_action": row["proposed_action"],
            "reason": row["action_reason"],
        }
        for row in records
        if int(row["size_bytes"]) >= LARGE_REVIEW_LIMIT
        or row["asset_class"] in {"model", "cache"}
        or row["proposed_action"] == "manual review"
    ]
    csv_write(
        AUDIT_DIR / "LARGE_OR_EXTERNAL_ASSETS_MANIFEST.csv",
        ["source_folder", "relative_path", "size_bytes", "sha256", "asset_class", "proposed_action", "reason"],
        large_external,
    )

    by_hash: dict[str, list[dict[str, object]]] = defaultdict(list)
    by_relative: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in records:
        if ".git/" not in str(row["relative_path"]) and not str(row["relative_path"]).startswith(".git/"):
            by_hash[str(row["sha256"])].append(row)
            by_relative[str(row["relative_path"])].append(row)
    duplicate_rows: list[dict[str, object]] = []
    group_id = 0
    for digest, members in sorted(by_hash.items()):
        if len(members) < 2:
            continue
        group_id += 1
        member_paths = ";".join(f"{m['source_folder']}/{m['relative_path']}" for m in members)
        duplicate_rows.append(
            {
                "duplicate_group": group_id,
                "sha256": digest,
                "size_bytes": members[0]["size_bytes"],
                "file_count": len(members),
                "paths": member_paths,
            }
        )
    csv_write(
        AUDIT_DIR / "DUPLICATE_FILE_GROUPS.csv",
        ["duplicate_group", "sha256", "size_bytes", "file_count", "paths"],
        duplicate_rows,
    )
    conflict_rows: list[dict[str, object]] = []
    for relative, members in sorted(by_relative.items()):
        hashes = {str(member["sha256"]) for member in members}
        folders = {str(member["source_folder"]) for member in members}
        if len(folders) > 1 and len(hashes) > 1:
            conflict_rows.append(
                {
                    "relative_path": relative,
                    "folder_count": len(folders),
                    "distinct_hashes": len(hashes),
                    "versions": ";".join(
                        f"{m['source_folder']}:{str(m['sha256'])[:12]}:{m['size_bytes']}" for m in members
                    ),
                }
            )
    csv_write(
        AUDIT_DIR / "RELATIVE_PATH_CONFLICTS.csv",
        ["relative_path", "folder_count", "distinct_hashes", "versions"],
        conflict_rows,
    )
    unique_rows: list[dict[str, object]] = []
    for relative, members in sorted(by_relative.items()):
        folders = {str(member["source_folder"]) for member in members}
        if len(folders) == 1:
            for member in members:
                unique_rows.append(
                    {
                        "source_folder": member["source_folder"],
                        "relative_path": relative,
                        "size_bytes": member["size_bytes"],
                        "sha256": member["sha256"],
                        "asset_class": member["asset_class"],
                    }
                )
    csv_write(
        AUDIT_DIR / "UNIQUE_FILES_BY_FOLDER.csv",
        ["source_folder", "relative_path", "size_bytes", "sha256", "asset_class"],
        unique_rows,
    )


def write_logical_snapshot_comparison(records: list[dict[str, object]]) -> None:
    cleanup_prefixes = [
        (
            "cleanup_nested_reviewer_artifact",
            "root_before_cleanup/submission_package/neurips2026_reviewer_artifact_anonymous/",
        ),
        ("cleanup_prior_reviewer_snapshot", "prior_reviewer_artifact_snapshot/"),
        ("cleanup_root_before", "root_before_cleanup/"),
    ]
    logical: dict[str, list[tuple[str, dict[str, object]]]] = defaultdict(list)
    for row in records:
        relative = str(row["relative_path"])
        if ".git" in relative.split("/") or row["proposed_action"] == "exclude" and Path(relative).name in OS_METADATA:
            continue
        if row["source_folder"] == SUBMITTED_FOLDER:
            logical[relative].append(("submitted_git_worktree", row))
            continue
        if row["source_folder"] != "cleanup_20260506_final_code_artifact_cleanup":
            continue
        for view, prefix in cleanup_prefixes:
            if relative.startswith(prefix):
                logical[relative[len(prefix):]].append((view, row))
                break
    conflicts: list[dict[str, object]] = []
    duplicates: list[dict[str, object]] = []
    for relative, members in sorted(logical.items()):
        views = {view for view, _ in members}
        hashes = {str(row["sha256"]) for _, row in members}
        if len(views) < 2:
            continue
        rendered = ";".join(
            f"{view}:{str(row['sha256'])[:12]}:{row['size_bytes']}:{row['source_folder']}/{row['relative_path']}"
            for view, row in members
        )
        target = conflicts if len(hashes) > 1 else duplicates
        target.append(
            {
                "logical_relative_path": relative,
                "snapshot_count": len(views),
                "distinct_hashes": len(hashes),
                "versions": rendered,
            }
        )
    fields = ["logical_relative_path", "snapshot_count", "distinct_hashes", "versions"]
    csv_write(AUDIT_DIR / "LOGICAL_SNAPSHOT_CONFLICTS.csv", fields, conflicts)
    csv_write(AUDIT_DIR / "LOGICAL_SNAPSHOT_DUPLICATES.csv", fields, duplicates)
    scientific_terms = (
        "human", "label", "scorer", "dataset", "config", "requirement", "test",
        "figure", "table", ".tex", ".py", ".csv", ".json", ".jsonl",
    )
    high_value = [
        row for row in conflicts
        if any(term in str(row["logical_relative_path"]).lower() for term in scientific_terms)
    ]
    report = [
        "# Logical Snapshot Comparison",
        "",
        "The cleanup folder contains three nested project snapshots. This comparison strips those wrapper prefixes before comparing them to the submitted Git worktree.",
        "",
        f"- Same logical paths with identical hashes: **{len(duplicates)}**",
        f"- Same logical paths with conflicting hashes: **{len(conflicts)}**",
        f"- Scientifically relevant logical conflicts: **{len(high_value)}**",
        "",
        "## Scientifically relevant conflicts",
        "",
    ]
    for row in high_value[:200]:
        report.append(f"- `{row['logical_relative_path']}` — {row['snapshot_count']} snapshots, {row['distinct_hashes']} hashes")
    if len(high_value) > 200:
        report.append(f"- … {len(high_value) - 200} additional conflicts are in `LOGICAL_SNAPSHOT_CONFLICTS.csv`.")
    report.extend(
        [
            "",
            "No version is selected as authoritative. Use nested Git provenance, generation commands, source traces, and output hashes before adopting any remnant version.",
            "",
        ]
    )
    (AUDIT_DIR / "LOGICAL_SNAPSHOT_COMPARISON.md").write_text("\n".join(report), encoding="utf-8")


def evidence_paths(records: list[dict[str, object]], terms: tuple[str, ...], limit: int = 12) -> list[str]:
    paths: list[str] = []
    for row in records:
        if row["proposed_action"] == "exclude" and ".git" in str(row["relative_path"]).split("/"):
            continue
        value = f"{row['source_folder']}/{row['relative_path']}"
        lowered = value.lower()
        if any(term in lowered for term in terms):
            paths.append(value)
    return paths[:limit]


def write_scientific_reports(
    records: list[dict[str, object]],
    excluded: list[dict[str, object]],
    scan_findings: dict[str, list[str]],
    nested_repos: list[str],
) -> None:
    by_folder: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in records:
        if ".git" not in str(row["relative_path"]).split("/"):
            by_folder[str(row["source_folder"])].append(row)
    counts = {folder: len(rows) for folder, rows in by_folder.items()}
    sizes = {folder: sum(int(row["size_bytes"]) for row in rows) for folder, rows in by_folder.items()}
    category_counts = {
        folder: Counter(str(row["asset_class"]) for row in rows)
        for folder, rows in by_folder.items()
    }
    reports = {
        "results": evidence_paths(records, ("result", "metric", "score", "per_query")),
        "human": evidence_paths(records, ("human", "annotation", "label")),
        "datasets": evidence_paths(records, ("dataset", "data/", "manifest")),
        "scripts": evidence_paths(records, ("scripts/", ".py")),
        "paper": evidence_paths(records, (".tex", ".bib", ".pdf", "paper")),
        "longform": evidence_paths(records, ("longform", "multi_hop", "multihop", "stress")),
        "judges": evidence_paths(records, ("judge", "llm_eval", "scorer", "nli")),
        "retrievers": evidence_paths(records, ("retriever", "retrieval")),
        "generators": evidence_paths(records, ("generator", "generation", "second_generator")),
        "cost": evidence_paths(records, ("cost", "latency", "token")),
        "conflicting": evidence_paths(records, ("conflict", "contradict", "disagreement")),
        "requirements": evidence_paths(records, ("requirements", "environment", "pyproject")),
    }
    asset_lines = [
        "# Scientific Asset Index",
        "",
        "This path-driven index inventories evidence; it does not validate scientific claims.",
        "",
    ]
    for title, key in [
        ("Paper sources and compiled papers", "paper"),
        ("Experiment scripts and source", "scripts"),
        ("Results, metrics, and per-query outputs", "results"),
        ("Human-evaluation and annotations", "human"),
        ("Dataset material and manifests", "datasets"),
        ("Judge/scorer implementations", "judges"),
        ("Long-form, multi-hop, or stress evidence", "longform"),
        ("Alternate generator evidence", "generators"),
        ("Retriever evidence", "retrievers"),
        ("Cost/latency evidence", "cost"),
        ("Conflicting-evidence or disagreement evidence", "conflicting"),
        ("Requirements and environments", "requirements"),
    ]:
        asset_lines.extend([f"## {title}", "", markdown_list(reports[key]), ""])
    (AUDIT_DIR / "SCIENTIFIC_ASSET_INDEX.md").write_text("\n".join(asset_lines), encoding="utf-8")

    provenance = [
        "# Folder Provenance and Role Inference",
        "",
        "Roles are inferred from Git state, names, internal manifests, and file layout. No files were merged to make these inferences.",
        "",
        f"## `{SUBMITTED_FOLDER}`",
        "",
        "- **Inferred role:** exact submitted/reviewer artifact working tree.",
        "- **Evidence:** the only nested Git repository; clean `main` at `59e94a5418a296acda1892e9165fd43096292f58`; latest commit subject is `Restore reviewer artifact submission package`; contains `artifact_manifest.md`, `SOURCE_TRACE.md`, `README_REPRODUCE.md`, paper sources, scripts, and consolidated results.",
        "- **Baseline treatment:** copied byte-for-byte except nested Git metadata and any separately manifested safety exclusions. No scientific repairs were applied.",
        "",
        "## `cleanup_20260506_final_code_artifact_cleanup`",
        "",
        "- **Inferred role:** pre-cleanup capture and cleanup planning worktree.",
        "- **Evidence:** `CLEANUP_PLAN.md`, `root_before_cleanup/`, and the largest number of scientific files/results. It preserves substantially more experiment state than the submitted artifact.",
        "",
        "## `deleted_from_head`",
        "",
        "- **Inferred role:** files intentionally removed from a prior repository HEAD but retained for forensic recovery.",
        "- **Evidence:** archive/log-oriented layout and absence of a nested Git root.",
        "",
        "## `moved_from_repo`",
        "",
        "- **Inferred role:** material moved out of the active repository, including paper/submission packages and a generated Chroma database.",
        "- **Evidence:** `submission_package*`, paper archives, and `chroma_db/` paths.",
        "",
        "## Completeness versus reproducibility",
        "",
        f"- **Most complete scientific state by file/result coverage:** `cleanup_20260506_final_code_artifact_cleanup` ({counts.get(SOURCE_FOLDERS[0], 0)} non-Git files; {category_counts.get(SOURCE_FOLDERS[0], Counter()).get('result', 0)} result-classified files).",
        f"- **Most reproducible bounded baseline:** `{SUBMITTED_FOLDER}` because it is the clean, documented Git snapshot, though its manifests and checks still require validation.",
        "- Completeness does not imply authority: remnant versions remain separate and conflicts are not resolved here.",
        "",
    ]
    (AUDIT_DIR / "FOLDER_PROVENANCE_AND_ROLE_INFERENCE.md").write_text("\n".join(provenance), encoding="utf-8")

    comparison_rows = []
    for folder in SOURCE_FOLDERS:
        comparison_rows.append(
            f"- `{folder}`: {counts.get(folder, 0):,} files, {sizes.get(folder, 0):,} bytes; "
            f"{category_counts.get(folder, Counter()).get('source', 0)} source, "
            f"{category_counts.get(folder, Counter()).get('data', 0)} data, "
            f"{category_counts.get(folder, Counter()).get('result', 0)} result, "
            f"{category_counts.get(folder, Counter()).get('paper', 0)} paper-classified."
        )
    cross = [
        "# Cross-Folder Diff Summary",
        "",
        *comparison_rows,
        "",
        "Exact duplicates, path conflicts, and folder-unique files are enumerated in `DUPLICATE_FILE_GROUPS.csv`, `RELATIVE_PATH_CONFLICTS.csv`, and `UNIQUE_FILES_BY_FOLDER.csv`.",
        "",
        "The cleanup capture contains the broadest experiment/result surface. The submitted artifact is a smaller, clean Git snapshot. The moved and deleted folders preserve omitted packages, logs, and generated state. This audit does not assert that newer timestamps or larger coverage make a remnant scientifically correct.",
        "",
    ]
    (AUDIT_DIR / "CROSS_FOLDER_DIFF_SUMMARY.md").write_text("\n".join(cross), encoding="utf-8")

    submitted_relatives = {
        str(row["relative_path"]) for row in by_folder.get(SUBMITTED_FOLDER, [])
    }
    remnant_gaps = [
        f"{row['source_folder']}/{row['relative_path']}"
        for row in records
        if row["source_folder"] != SUBMITTED_FOLDER
        and ".git" not in str(row["relative_path"]).split("/")
        and str(row["relative_path"]) not in submitted_relatives
        and row["asset_class"] in {"source", "data", "result", "notebook", "paper", "environment"}
    ]
    load_bearing = [
        "# Load-Bearing Asset Gaps",
        "",
        "The following are candidate gaps, not automatically authoritative replacements. They are absent at the same relative path from the submitted artifact and should be traced before any merge.",
        "",
        markdown_list(remnant_gaps, 100),
        "",
        "Key integrity questions remain: whether every paper table has a source result; whether each result has a generating command/config; and whether human labels/scorer inputs are version-aligned. Resolve using hashes and source traces before changing claims.",
        "",
    ]
    (AUDIT_DIR / "LOAD_BEARING_ASSET_GAPS.md").write_text("\n".join(load_bearing), encoding="utf-8")

    conflict_terms = ("human", "label", "scorer", "dataset", "config", "requirement", "test", "figure", "table", ".tex", ".py")
    conflict_paths: list[str] = []
    relative_map: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in records:
        if ".git" not in str(row["relative_path"]).split("/"):
            relative_map[str(row["relative_path"])].append(row)
    for relative, members in relative_map.items():
        if len({str(member["source_folder"]) for member in members}) > 1 and len({str(member["sha256"]) for member in members}) > 1:
            if any(term in relative.lower() for term in conflict_terms):
                conflict_paths.append(relative)
    conflict_report = [
        "# Conflicting Scientific Versions",
        "",
        "Same-relative-path files with different SHA-256 hashes are potential version conflicts. No winner was selected.",
        "",
        markdown_list(sorted(conflict_paths), 100),
        "",
        "See `RELATIVE_PATH_CONFLICTS.csv` for every version hash and source folder.",
        "",
    ]
    (AUDIT_DIR / "CONFLICTING_SCIENTIFIC_VERSIONS.md").write_text("\n".join(conflict_report), encoding="utf-8")

    recoverable = [
        "# Recoverable Missing Evidence",
        "",
        "High-value evidence candidates found outside the submitted artifact:",
        "",
        "## Per-query and detailed result material",
        "",
        markdown_list([path for path in remnant_gaps if any(term in path.lower() for term in ("per_query", "result", "metric"))], 50),
        "",
        "## Human evaluation and calibration",
        "",
        markdown_list([path for path in remnant_gaps if any(term in path.lower() for term in ("human", "label", "calibration", "correlation"))], 50),
        "",
        "## Broader-scope experiments",
        "",
        markdown_list([path for path in remnant_gaps if any(term in path.lower() for term in ("longform", "stress", "generator", "retriever", "conflict", "multihop"))], 50),
        "",
        "Each candidate requires provenance and script-to-output validation before use in a rebuttal or revision.",
        "",
    ]
    (AUDIT_DIR / "RECOVERABLE_MISSING_EVIDENCE.md").write_text("\n".join(recoverable), encoding="utf-8")

    concern_specs = [
        ("Narrow empirical scope and generalizability", ("longform", "stress", "generator", "retriever"), "partially answered"),
        ("Dependence on short-answer/single-hop QA", ("longform", "multihop", "multi_hop", "stress"), "partially answered"),
        ("Lack of newer LLM judges/task-specific evaluators", ("judge", "scorer", "nli", "ragas"), "partially answered"),
        ("Uneven evidence across system factors and cost", ("generator", "retriever", "context", "scorer", "human", "cost"), "partially answered"),
        ("Missing practitioner guidance for disagreements", ("disagreement", "guidance", "decision"), "partially answered"),
        ("Dense or unclear metric descriptions", ("metric", "README_REPRODUCE", ".tex"), "partially answered"),
        ("Weak justification for exactly seven axes", ("axis", "axes", "seven"), "unanswered"),
        ("Unclear dataset and experiment descriptions", ("dataset", "experiment", "manifest"), "partially answered"),
        ("Chaotic or difficult-to-navigate codebase", ("README", "manifest", "SOURCE_TRACE"), "partially answered"),
        ("Missing conflicting-evidence work/experiments", ("conflict", "contradict", "disagreement"), "partially answered"),
        ("Scorer input format and human calibration", ("human", "calibration", "correlation", "scorer"), "partially answered"),
        ("Annotation provenance or wording inconsistency", ("annotation", "label", "human"), "partially answered"),
        ("Prompt-injection or publication-safety issue", ("prompt", "injection", "system"), "partially answered"),
        ("Missing per-query files or broken source trace", ("per_query", "SOURCE_TRACE", "manifest"), "partially answered"),
    ]
    concern_lines = [
        "# Review and Meta-Review Concern Matrix",
        "",
        "Statuses are conservative path/evidence assessments. Scientific sufficiency still requires manual claim-level validation.",
        "",
    ]
    experiment_rows: list[dict[str, object]] = []
    for concern, terms, default_status in concern_specs:
        paths = evidence_paths(records, terms, 8)
        status = default_status if paths else "unanswered"
        concern_lines.extend(
            [
                f"## {concern}",
                "",
                f"- **Status:** {status}",
                f"- **Existing evidence:** {', '.join(f'`{path}`' for path in paths) if paths else 'None located by deterministic path scan.'}",
                "- **Lowest-risk clarification:** map the exact paper claim to the existing artifact path, command, configuration, and hash.",
                "- **Smallest credible analysis:** validate the relevant per-query outputs and report uncertainty/error slices without changing the baseline.",
                "- **Smallest credible experiment:** run only the narrow missing comparison after provenance and dependency checks.",
                "- **Estimated compute/time:** clarification 1–3 hours; analysis 2–8 CPU-hours; new model experiment may require 2–24 GPU-hours plus API cost.",
                "- **Use:** NeurIPS rebuttal for factual clarification; EACL revision for broader experiments.",
                "- **Risk:** remnant outputs may not match the submitted code/configuration and must not be cited before trace validation.",
                "",
            ]
        )
        for path in paths or [""]:
            experiment_rows.append(
                {
                    "review_concern": concern,
                    "status": status,
                    "evidence_path": path,
                    "source_folder": path.split("/", 1)[0] if path else "",
                    "evidence_kind": classify_asset(Path(path)).title() if path else "None",
                    "validation_required": "claim-to-output and script/config/hash trace",
                    "rebuttal_or_revision": "both",
                }
            )
    (AUDIT_DIR / "REVIEW_AND_META_REVIEW_CONCERN_MATRIX.md").write_text("\n".join(concern_lines), encoding="utf-8")
    csv_write(
        AUDIT_DIR / "EXPERIMENT_EVIDENCE_MATRIX.csv",
        [
            "review_concern", "status", "evidence_path", "source_folder",
            "evidence_kind", "validation_required", "rebuttal_or_revision",
        ],
        experiment_rows,
    )

    rebuttal = [
        "# NeurIPS Rebuttal Readiness",
        "",
        "## Ready for low-risk clarification",
        "",
        "- Submitted baseline identity and Git commit can be stated precisely.",
        "- Existing source traces, manifests, requirements, scripts, consolidated results, and human-evaluation material can be mapped to reviewer questions.",
        "- Remnant folders contain candidate evidence for broader scope, retriever/generator sensitivity, long-form stress, scorer disagreement, calibration, and cost.",
        "",
        "## Not yet ready for scientific assertion",
        "",
        "- Remnant outputs have not been proven to originate from the submitted code/configuration.",
        "- Same-path conflicts have not been adjudicated.",
        "- Full paper claim-to-result-to-command trace has not been manually verified.",
        "- Lightweight checks cannot establish experimental correctness.",
        "",
        "## Highest-value immediate work",
        "",
        "Validate the paper’s most reviewer-relevant tables against per-query files, generating scripts, configs, and hashes; then identify which remnant analyses are reproducible without new model generation.",
        "",
    ]
    (AUDIT_DIR / "NEURIPS_REBUTTAL_READINESS.md").write_text("\n".join(rebuttal), encoding="utf-8")

    eacl = [
        "# EACL Upgrade Opportunities",
        "",
        "1. Expand beyond short-answer/single-hop settings using the recovered long-form/stress paths after provenance validation.",
        "2. Add current, clearly documented LLM judges and task-specific evaluators with scorer-input-format ablations.",
        "3. Validate alternate generators and retrievers across all axes rather than isolated aggregates.",
        "4. Add conflicting-evidence conditions and actionable practitioner guidance for metric disagreement.",
        "5. Strengthen scorer-to-human calibration, threshold transfer, confidence intervals, and annotation provenance.",
        "6. Publish a deterministic claim/table/figure-to-command-to-output map and a clean environment lock.",
        "",
        "These are revision opportunities, not claims supported merely by this audit.",
        "",
    ]
    (AUDIT_DIR / "EACL_UPGRADE_OPPORTUNITIES.md").write_text("\n".join(eacl), encoding="utf-8")

    credential_findings = [
        finding for finding in scan_findings.get("secrets", [])
        if "personal_email" not in finding
    ]
    personal_email_findings = [
        finding for finding in scan_findings.get("secrets", [])
        if "personal_email" in finding
    ]
    safety = [
        "# Publication Safety Audit",
        "",
        f"- Source files inventoried: {len(records):,}.",
        f"- Files excluded or held for manual review: {len(excluded):,}.",
        f"- Nested repositories detected: {', '.join(f'`{name}`' for name in nested_repos) if nested_repos else 'none'}.",
        f"- High-confidence credential-bearing files: {len(credential_findings)}.",
        f"- Files containing the owner's personal email: {len(personal_email_findings)}.",
        f"- Files containing prompt-injection phrases: {len(scan_findings.get('prompt_injection', []))}.",
        f"- Files containing absolute macOS home paths: {len(scan_findings.get('home_paths', []))}.",
        "",
        "## Credential findings",
        "",
        markdown_list(credential_findings, 100),
        "",
        "## Personal email findings",
        "",
        markdown_list(personal_email_findings, 100),
        "",
        "## Prompt-injection phrase findings",
        "",
        markdown_list(scan_findings.get("prompt_injection", []), 100),
        "",
        "These phrases are preserved in safe source files for forensic integrity and are treated as data, not instructions.",
        "",
        "## Absolute home-path findings",
        "",
        markdown_list(scan_findings.get("home_paths", []), 100),
        "",
        "Absolute paths are a privacy/reproducibility warning. Baseline source files were not silently rewritten; publication decisions are recorded in the safety classification.",
        "",
    ]
    (AUDIT_DIR / "PUBLICATION_SAFETY_AUDIT.md").write_text("\n".join(safety), encoding="utf-8")

    secret_summary = [
        "# Secret Scan Summary",
        "",
        f"Automated high-confidence credential findings: **{len(credential_findings)}**.",
        f"Owner personal-email findings: **{len(personal_email_findings)}**.",
        "",
        "## Credential findings",
        "",
        markdown_list(credential_findings, 100),
        "",
        "## Personal email findings",
        "",
        markdown_list(personal_email_findings, 100),
        "",
        "Files with high-confidence credential or owner-email findings were excluded from the publication copy and remain listed by path, size, and SHA-256 in `EXCLUDED_FILES_MANIFEST.csv`. Regex scanning reduces risk but does not prove absence of secrets; staged-content scans are run again before push.",
        "",
    ]
    (AUDIT_DIR / "SECRET_SCAN_SUMMARY.md").write_text("\n".join(secret_summary), encoding="utf-8")

    license_paths = [
        f"{row['source_folder']}/{row['relative_path']}"
        for row in records
        if Path(str(row["relative_path"])).name.lower().startswith(("license", "copying", "notice"))
    ]
    license_report = [
        "# License and Redistribution Notes",
        "",
        "License files detected:",
        "",
        markdown_list(license_paths, 100),
        "",
        "No license inference is made for folders lacking an explicit license. Third-party datasets, model weights, caches, and archives remain subject to their own terms. Generated Chroma/vector database state was excluded and manifested. Before making the repository public, a maintainer should confirm redistribution rights for bundled datasets, PDFs, archives, figures, and external model outputs.",
        "",
    ]
    (AUDIT_DIR / "LICENSE_AND_REDISTRIBUTION_NOTES.md").write_text("\n".join(license_report), encoding="utf-8")


def write_health_placeholders(records: list[dict[str, object]]) -> None:
    existing_results = AUDIT_DIR / "TEST_RESULTS.csv"
    if existing_results.exists() and len(existing_results.read_text(encoding="utf-8").splitlines()) > 1:
        return
    configs = evidence_paths(records, ("requirements", "pyproject", "setup.py", "environment", "dockerfile"), 100)
    health = [
        "# Technical Health Report",
        "",
        "This file is finalized by the lightweight-check phase after copying. No model downloads, package installs, dataset downloads, or experiments are permitted.",
        "",
        "Detected environment/configuration files:",
        "",
        markdown_list(configs, 100),
        "",
    ]
    (AUDIT_DIR / "TECHNICAL_HEALTH_REPORT.md").write_text("\n".join(health), encoding="utf-8")
    (AUDIT_DIR / "TEST_AND_SMOKE_COMMANDS.md").write_text(
        "# Test and Smoke Commands\n\nPending execution in the isolated ingest workspace.\n",
        encoding="utf-8",
    )
    csv_write(
        AUDIT_DIR / "TEST_RESULTS.csv",
        ["source_folder", "check", "command", "status", "duration_seconds", "summary"],
        [],
    )
    (AUDIT_DIR / "DEPENDENCY_GAPS.md").write_text(
        "# Dependency Gaps\n\nPending static import and configuration analysis.\n",
        encoding="utf-8",
    )
    (AUDIT_DIR / "REPRODUCIBILITY_BLOCKERS.md").write_text(
        "# Reproducibility Blockers\n\nPending lightweight checks and manual source-trace validation.\n",
        encoding="utf-8",
    )


def write_root_documents(records: list[dict[str, object]], excluded: list[dict[str, object]]) -> None:
    readme = f"""# RAG Hallucination Project — Preserved Forensic Snapshot

This repository preserves four distinct local project remnants for collaborator inspection before any scientific repair, rerun, or rewrite.

## Source folders

- `{SUBMITTED_FOLDER}/` — the NeurIPS anonymous/reviewer artifact baseline. It is preserved as submitted and has not been silently repaired.
- `cleanup_20260506_final_code_artifact_cleanup/` — cleanup-era material, including a pre-cleanup tree with broader experiment state.
- `deleted_from_head/` — material recovered or retained after deletion from a prior HEAD.
- `moved_from_repo/` — material moved out of the prior repository, including submission/paper packages and external/generated state.

Folder roles are evidence-based inferences documented in `audit/FOLDER_PROVENANCE_AND_ROLE_INFERENCE.md`. A larger or newer remnant is not automatically more scientifically authoritative.

## Navigate the audit

- Start with `audit/GITHUB_INGEST_REPORT.md`, `audit/FOLDER_PROVENANCE_AND_ROLE_INFERENCE.md`, and `audit/NEXT_ACTION_PLAN.md`.
- File-level hashes, classifications, exclusions, duplicates, and conflicts are in the CSV manifests under `audit/`.
- Technical checks and reproducibility blockers are in `audit/TECHNICAL_HEALTH_REPORT.md` and `audit/REPRODUCIBILITY_BLOCKERS.md`.
- Reviewer-readiness evidence is mapped in `audit/REVIEW_AND_META_REVIEW_CONCERN_MATRIX.md`.

## Preservation and exclusions

No cross-folder scientific merge has occurred. Nested `.git/` directories, caches, credentials, unsafe private material, and unsuitable large/generated assets are excluded from the copied working trees. Every exclusion is retained by source folder, relative path, byte size, SHA-256, and reason in `audit/EXCLUDED_FILES_MANIFEST.csv`; large/external assets are also listed in `audit/LARGE_OR_EXTERNAL_ASSETS_MANIFEST.csv`.

The source manifest `SOURCE_SNAPSHOT_MANIFEST.sha256` covers the included files in all four preserved trees.

## Next step

Externally inspect this snapshot, then validate claim-to-table-to-result-to-command provenance before selecting any remnant analysis for the NeurIPS rebuttal or any broader experiment for an EACL revision.
"""
    (REPO_ROOT / "README.md").write_text(readme, encoding="utf-8")
    baseline = f"""# Submitted Artifact Baseline

The exact local folder identified as the NeurIPS anonymous/reviewer artifact is:

`{SUBMITTED_FOLDER}/`

Evidence:

- it is the only one of the four source folders with a nested Git repository;
- it is on clean branch `main` at commit `59e94a5418a296acda1892e9165fd43096292f58`;
- the latest commit is titled `Restore reviewer artifact submission package`;
- it contains `artifact_manifest.md`, `SOURCE_TRACE.md`, `README_REPRODUCE.md`, requirements, paper sources, scripts, and results.

The working tree is preserved as a baseline, not silently repaired. Nested `.git/` internals are not copied; their branch, commit, status, log, tags, remotes (redacted), submodule, shallow, ignored, and LFS state are exported under `audit/`. Any safety exclusion is explicit in `audit/EXCLUDED_FILES_MANIFEST.csv`.
"""
    (REPO_ROOT / "BASELINE_SUBMITTED_ARTIFACT.md").write_text(baseline, encoding="utf-8")

    next_plan = f"""# Next Action Plan

## P0: Integrity and factual blockers

1. **Validate paper claim/table/figure provenance.** Trace every headline paper value through `{SUBMITTED_FOLDER}/SOURCE_TRACE.md`, `{SUBMITTED_FOLDER}/artifact_manifest.md`, generating scripts, configs, and hashed outputs. Dependencies: no new model runs; use the manifests and per-query files. Estimate: 4–12 CPU-hours. Risk: high if mappings disagree. Addresses source-trace, missing per-query, and factual-integrity concerns. Does not change claims unless a mismatch is found.
2. **Adjudicate same-path scientific conflicts.** Use `audit/RELATIVE_PATH_CONFLICTS.csv` and prioritize human labels, scorers, dataset preparation, configs, paper sources, requirements, and tests. Estimate: 4–8 CPU-hours; no GPU. Risk: selecting by timestamp instead of provenance. Addresses annotation/scorer/reproducibility concerns. May change claims only if current evidence is inconsistent.
3. **Manually clear publication/license holds.** Review `audit/EXCLUDED_FILES_MANIFEST.csv`, `audit/SECRET_SCAN_SUMMARY.md`, and `audit/LICENSE_AND_REDISTRIBUTION_NOTES.md`; rotate any real credential. Estimate: 1–3 hours. No compute. Does not change scientific claims.

## P1: NeurIPS rebuttal-critical clarifications/analyses

1. Map reviewer concerns to exact existing evidence using `audit/REVIEW_AND_META_REVIEW_CONCERN_MATRIX.md` and validate uncertainty at per-query level. Estimate: 4–10 CPU-hours. Low scientific risk if limited to verified outputs; no claim change unless corrections are required.
2. Validate scorer-to-human calibration and disagreement files under `{SUBMITTED_FOLDER}/human_eval_final/`, `{SUBMITTED_FOLDER}/results/revision/fix_03/`, and corresponding cleanup-tree paths. Estimate: 4–12 CPU-hours; no GPU expected. Addresses calibration and scorer-input interpretation.
3. Extract the smallest defensible cost, generator, retriever, and stress-test analyses from verified existing outputs. Estimate: 4–8 CPU-hours. No new claim until provenance is complete.

## P2: Fastest credible new experiments

1. Re-run only lightweight deterministic analyses whose inputs are already present (confidence intervals, error slices, threshold-transfer checks). Estimate: 2–8 CPU-hours. Risk: version skew; pin exact input hashes. May strengthen or narrow claims.
2. If credentials/compute are approved, run one current judge on a fixed, pre-hashed sample with explicit input formatting. Estimate: 2–8 GPU/API-hours. Risk: cost, nondeterminism, evaluator leakage. Adds a scoped new claim.

## P3: EACL-strengthening experiments

1. Validate and extend recovered long-form/multi-hop/stress, alternate-generator, alternate-retriever, and conflicting-evidence pipelines. Exact candidate paths are in `audit/RECOVERABLE_MISSING_EVIDENCE.md`. Estimate: 1–5 GPU-days plus API cost. Medium/high integrity risk until remnant provenance is resolved. Expands scientific scope.
2. Add modern judges, task-specific evaluators, repeated seeds, scorer-to-human calibration, threshold transfer, and full cost reporting. Estimate: 2–10 GPU-days/API equivalent. Changes and broadens claims.

## P4: Repository cleanup and paper rewrite

1. On a new branch, create one canonical package layout, locked environment, deterministic entry points, tests, and a claim-to-artifact map. Preserve `{SUBMITTED_FOLDER}/` unchanged. Estimate: 2–5 engineer-days. No GPU. Does not itself change claims.
2. Rewrite metric/dataset/experiment descriptions and practitioner guidance only after P0–P3 evidence is stable. Estimate: 2–4 researcher-days. Claims may be clarified or narrowed, never retrofitted to unverified remnants.
"""
    (AUDIT_DIR / "NEXT_ACTION_PLAN.md").write_text(next_plan, encoding="utf-8")

    ingest = f"""# GitHub Ingest Report

## Source

- Local source path (publication-redacted): `/Users/<redacted>/Projects/raghallucination`
- Expected source folders found: **{sum((SOURCE_ROOT / name).is_dir() for name in SOURCE_FOLDERS)}/4**
- Original source directories modified: **No**
- Submitted baseline: `{SUBMITTED_FOLDER}` at nested Git commit `59e94a5418a296acda1892e9165fd43096292f58`

## Snapshot

- Files inventoried (including excluded nested Git internals): {len(records):,}
- Files copied into the four publication trees: {sum(1 for row in records if row['proposed_action'] == 'include'):,}
- Files excluded or held: {len(excluded):,}
- Remote target: `https://github.com/Saket-Maganti/raghal.git`
- Remote state observed before ingest: empty repository
- Publication status: pending commit, push, tag, and remote verification

This report is updated after publication with the verified branch, commit, tag, file count, and remote accessibility.
"""
    (AUDIT_DIR / "GITHUB_INGEST_REPORT.md").write_text(ingest, encoding="utf-8")


def write_snapshot_manifest() -> None:
    lines: list[str] = []
    for folder in SOURCE_FOLDERS:
        base = REPO_ROOT / folder
        for path in sorted(base.rglob("*"), key=lambda item: item.relative_to(REPO_ROOT).as_posix()):
            if (
                path.is_file()
                and not path.is_symlink()
                and path.name not in OS_METADATA
                and not any(part in CACHE_PARTS for part in path.parts)
            ):
                lines.append(f"{sha256_file(path)}  {path.relative_to(REPO_ROOT).as_posix()}")
    (REPO_ROOT / "SOURCE_SNAPSHOT_MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    missing = [name for name in SOURCE_FOLDERS if not (SOURCE_ROOT / name).is_dir()]
    if missing:
        print(f"Missing expected source directories: {', '.join(missing)}", file=sys.stderr)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (LOCAL_WORKSPACE / "LOCAL_SOURCE_PATH.txt").write_text(
        f"{SOURCE_ROOT}\nGenerated: {datetime.now().astimezone().isoformat()}\n",
        encoding="utf-8",
    )
    for folder in SOURCE_FOLDERS:
        destination = REPO_ROOT / folder
        if destination.exists():
            safe_unlink_tree_contents(destination)
    _, _, nested_repos = git_provenance()
    records, excluded, scan_findings = build_inventory_and_copy()
    write_inventory_reports(records, excluded)
    write_logical_snapshot_comparison(records)
    write_scientific_reports(records, excluded, scan_findings, nested_repos)
    write_health_placeholders(records)
    write_root_documents(records, excluded)
    write_snapshot_manifest()
    print(
        json.dumps(
            {
                "source_folders_found": len(SOURCE_FOLDERS) - len(missing),
                "files_inventoried": len(records),
                "files_included": sum(1 for row in records if row["proposed_action"] == "include"),
                "files_excluded_or_held": len(excluded),
                "secret_bearing_files": len(scan_findings.get("secrets", [])),
                "prompt_injection_files": len(scan_findings.get("prompt_injection", [])),
                "home_path_files": len(scan_findings.get("home_paths", [])),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
