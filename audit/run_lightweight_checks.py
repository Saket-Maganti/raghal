#!/usr/bin/env python3
"""Run bounded, non-destructive health checks against the staged snapshot."""

from __future__ import annotations

import csv
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit"
TEMP = ROOT.parent / "audit_check_tmp"
TEMP.mkdir(parents=True, exist_ok=True)


def execute(
    source_folder: str,
    check: str,
    command: list[str],
    cwd: Path,
    timeout: int = 120,
    env_extra: dict[str, str] | None = None,
) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONPYCACHEPREFIX"] = str(TEMP / "pycache")
    env["MPLCONFIGDIR"] = str(TEMP / "matplotlib")
    if env_extra:
        env.update(env_extra)
    started = time.monotonic()
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        status = "pass" if process.returncode == 0 else "fail"
        output = "\n".join(piece for piece in (process.stdout.strip(), process.stderr.strip()) if piece)
        summary = output[-1500:] if output else f"exit code {process.returncode}"
    except subprocess.TimeoutExpired as exc:
        status = "blocked"
        output = "\n".join(
            piece.decode(errors="replace") if isinstance(piece, bytes) else piece
            for piece in (exc.stdout or "", exc.stderr or "")
            if piece
        )
        summary = f"timed out after {timeout}s; {output[-1000:]}"
    return {
        "source_folder": source_folder,
        "check": check,
        "command": " ".join(command),
        "status": status,
        "duration_seconds": f"{time.monotonic() - started:.3f}",
        "summary": summary.replace("\x00", ""),
    }


def internal_result(
    source_folder: str,
    check: str,
    command: str,
    status: str,
    started: float,
    summary: str,
) -> dict[str, object]:
    return {
        "source_folder": source_folder,
        "check": check,
        "command": command,
        "status": status,
        "duration_seconds": f"{time.monotonic() - started:.3f}",
        "summary": summary,
    }


def main() -> int:
    results: list[dict[str, object]] = []
    compile_roots = [
        "cleanup_20260506_final_code_artifact_cleanup",
        "deleted_from_head",
        "moved_from_repo",
        "rag-hallucination-detection_main",
    ]
    for folder in compile_roots:
        results.append(
            execute(
                folder,
                "python compileall",
                [sys.executable, "-m", "compileall", "-q", "."],
                ROOT / folder,
                timeout=180,
            )
        )

    notebook_root = ROOT / "moved_from_repo" / "notebooks"
    started = time.monotonic()
    notebook_errors: list[str] = []
    notebook_count = 0
    for notebook in sorted(notebook_root.glob("*.ipynb")):
        notebook_count += 1
        try:
            payload = json.loads(notebook.read_text(encoding="utf-8"))
            if not isinstance(payload.get("cells"), list) or not isinstance(payload.get("metadata"), dict):
                notebook_errors.append(f"{notebook.name}: missing cells/metadata structure")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            notebook_errors.append(f"{notebook.name}: {exc}")
    results.append(
        internal_result(
            "moved_from_repo",
            "notebook JSON validation",
            "json.loads + notebook structural keys",
            "pass" if not notebook_errors else "fail",
            started,
            f"validated {notebook_count} notebooks"
            if not notebook_errors
            else "; ".join(notebook_errors),
        )
    )

    shell_scripts = sorted(ROOT.glob("**/*.sh"))
    started = time.monotonic()
    shell_errors: list[str] = []
    for script in shell_scripts:
        process = subprocess.run(
            ["bash", "-n", str(script)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if process.returncode:
            shell_errors.append(f"{script.relative_to(ROOT)}: {(process.stderr or process.stdout).strip()}")
    results.append(
        internal_result(
            "all",
            "shell syntax",
            "bash -n <each .sh>",
            "pass" if not shell_errors else "fail",
            started,
            f"validated {len(shell_scripts)} shell scripts"
            if not shell_errors
            else "; ".join(shell_errors)[:1500],
        )
    )

    toml_paths = sorted(ROOT.glob("**/*.toml"))
    started = time.monotonic()
    toml_errors: list[str] = []
    for path in toml_paths:
        try:
            tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            toml_errors.append(f"{path.relative_to(ROOT)}: {exc}")
    results.append(
        internal_result(
            "all",
            "TOML parsing",
            "tomllib.loads <each .toml>",
            "pass" if not toml_errors else "fail",
            started,
            f"validated {len(toml_paths)} TOML files" if not toml_errors else "; ".join(toml_errors),
        )
    )

    project_roots = [
        (
            "rag-hallucination-detection_main",
            ROOT / "rag-hallucination-detection_main",
            ["tests"],
            ["tests"],
        ),
        (
            "cleanup_20260506_final_code_artifact_cleanup/prior_reviewer_artifact_snapshot",
            ROOT / "cleanup_20260506_final_code_artifact_cleanup" / "prior_reviewer_artifact_snapshot",
            ["tests"],
            ["tests"],
        ),
        (
            "cleanup_20260506_final_code_artifact_cleanup/root_before_cleanup",
            ROOT / "cleanup_20260506_final_code_artifact_cleanup" / "root_before_cleanup",
            ["tests"],
            ["tests"],
        ),
        (
            "cleanup_20260506_final_code_artifact_cleanup/root_before_cleanup/submission_package/neurips2026_reviewer_artifact_anonymous",
            ROOT
            / "cleanup_20260506_final_code_artifact_cleanup"
            / "root_before_cleanup"
            / "submission_package"
            / "neurips2026_reviewer_artifact_anonymous",
            ["tests"],
            ["tests"],
        ),
        (
            "moved_from_repo",
            ROOT / "moved_from_repo",
            ["tests"],
            ["tests/test_lint_paper.py"],
        ),
        (
            "moved_from_repo/pip-package",
            ROOT / "moved_from_repo" / "pip-package",
            ["tests"],
            ["tests"],
        ),
    ]
    for label, cwd, collect_targets, safe_targets in project_roots:
        results.append(
            execute(
                label,
                "pytest collection",
                [sys.executable, "-m", "pytest", "--collect-only", "-q", *collect_targets],
                cwd,
                timeout=90,
            )
        )
        results.append(
            execute(
                label,
                "lightweight pytest",
                [sys.executable, "-m", "pytest", "-q", *safe_targets],
                cwd,
                timeout=120,
            )
        )

    results.append(
        execute(
            "rag-hallucination-detection_main",
            "import smoke",
            [sys.executable, "-c", "from src.ccs_gate_retriever import CCSGateRetriever; print(CCSGateRetriever.__name__)"],
            ROOT / "rag-hallucination-detection_main",
            timeout=30,
        )
    )
    results.append(
        execute(
            "moved_from_repo/pip-package",
            "import smoke",
            [sys.executable, "-c", "from context_coherence import ccs; print(ccs.__name__)"],
            ROOT / "moved_from_repo" / "pip-package",
            timeout=30,
            env_extra={"PYTHONPATH": str(ROOT / "moved_from_repo" / "pip-package" / "src")},
        )
    )
    pip_package = ROOT / "moved_from_repo" / "pip-package"
    pip_env = {"PYTHONPATH": str(pip_package / "src")}
    results.append(
        execute(
            "moved_from_repo/pip-package",
            "configured pytest collection",
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
            pip_package,
            timeout=60,
            env_extra=pip_env,
        )
    )
    results.append(
        execute(
            "moved_from_repo/pip-package",
            "configured lightweight pytest",
            [sys.executable, "-m", "pytest", "-q", "tests"],
            pip_package,
            timeout=60,
            env_extra=pip_env,
        )
    )

    submitted = ROOT / "rag-hallucination-detection_main"
    with tempfile.TemporaryDirectory(prefix="submitted_workflow_", dir=TEMP) as temporary:
        workflow_copy = Path(temporary) / "artifact"
        shutil.copytree(
            submitted,
            workflow_copy,
            ignore=shutil.ignore_patterns(".DS_Store", ".pytest_cache", "__pycache__"),
        )
        results.append(
            execute(
                "rag-hallucination-detection_main",
                "documented lightweight workflow",
                ["bash", "run_all_analysis.sh"],
                workflow_copy,
                timeout=120,
            )
        )

    requirement_paths = sorted(ROOT.glob("**/requirements*.txt"))
    dependency_rows: list[tuple[str, str, str]] = []
    dependency_name_re = re.compile(r"^\s*([A-Za-z0-9_.-]+)")
    for path in requirement_paths:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "-", "git+", "http")):
                continue
            match = dependency_name_re.match(stripped)
            if not match:
                continue
            package = match.group(1)
            try:
                installed = importlib.metadata.version(package)
                state = f"installed {installed}"
            except importlib.metadata.PackageNotFoundError:
                state = "not installed in audit environment"
            dependency_rows.append((str(path.relative_to(ROOT)), package, state))

    with (AUDIT / "TEST_RESULTS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_folder", "check", "command", "status", "duration_seconds", "summary"],
        )
        writer.writeheader()
        writer.writerows(results)

    passed = sum(row["status"] == "pass" for row in results)
    failed = sum(row["status"] == "fail" for row in results)
    blocked = sum(row["status"] == "blocked" for row in results)
    report_lines = [
        "# Technical Health Report",
        "",
        f"- Checks passed: **{passed}**",
        f"- Checks failed: **{failed}**",
        f"- Checks blocked/timed out: **{blocked}**",
        "- No dependencies, models, or datasets were downloaded.",
        "- Python bytecode was redirected outside the staged source trees.",
        "- Builder tests that mutate generated paper artifacts were collection-checked but not executed.",
        "",
        "## Results",
        "",
    ]
    for row in results:
        report_lines.extend(
            [
                f"### {row['source_folder']} — {row['check']}",
                "",
                f"- Status: **{str(row['status']).upper()}**",
                f"- Duration: {row['duration_seconds']} seconds",
                f"- Command: `{row['command']}`",
                "",
                "```text",
                str(row["summary"]) or "(no output)",
                "```",
                "",
            ]
        )
    (AUDIT / "TECHNICAL_HEALTH_REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")

    command_lines = [
        "# Test and Smoke Commands",
        "",
        "Commands were run from the listed staged source folder with bytecode and matplotlib caches redirected to the local-only audit workspace.",
        "",
    ]
    for row in results:
        command_lines.append(
            f"- `{row['source_folder']}` — **{row['status']}** — `{row['command']}` ({row['duration_seconds']}s)"
        )
    (AUDIT / "TEST_AND_SMOKE_COMMANDS.md").write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    missing_dependencies = [row for row in dependency_rows if row[2].startswith("not installed")]
    dependency_lines = [
        "# Dependency Gaps",
        "",
        f"Requirement declarations inspected: {len(requirement_paths)}.",
        f"Declared package entries not installed in the audit environment: {len(missing_dependencies)}.",
        "",
        "Absence here is an environment observation, not proof that a dependency declaration is wrong. No packages were installed during the audit.",
        "",
    ]
    for path, package, state in missing_dependencies:
        dependency_lines.append(f"- `{path}` — `{package}`: {state}.")
    (AUDIT / "DEPENDENCY_GAPS.md").write_text("\n".join(dependency_lines) + "\n", encoding="utf-8")

    failed_rows = [row for row in results if row["status"] != "pass"]
    blockers = [
        "# Reproducibility Blockers",
        "",
        "## Observed lightweight-check failures",
        "",
    ]
    if failed_rows:
        for row in failed_rows:
            blockers.append(
                f"- `{row['source_folder']}` / `{row['check']}`: {str(row['summary']).splitlines()[-1][:500]}"
            )
    else:
        blockers.append("- None in the bounded checks.")
    blockers.extend(
        [
            "",
            "## Scientific reproducibility blockers not resolved by smoke tests",
            "",
            "- Remnant outputs are not yet cryptographically traced to the submitted code/configuration.",
            "- Same-relative-path conflicts across folders remain unadjudicated.",
            "- A complete paper claim/table/figure-to-input-to-command map has not been manually verified.",
            "- External APIs, model versions, datasets, seeds, and hardware-dependent generation were not exercised.",
            "- Absolute local paths in scripts/logs may prevent fresh-clone execution.",
            "- Requirements are not a fully locked environment and several declared packages are absent from the audit environment.",
            "",
        ]
    )
    (AUDIT / "REPRODUCIBILITY_BLOCKERS.md").write_text("\n".join(blockers), encoding="utf-8")
    print(json.dumps({"pass": passed, "fail": failed, "blocked": blocked, "total": len(results)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
