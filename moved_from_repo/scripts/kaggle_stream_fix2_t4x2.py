#!/usr/bin/env python3
"""Run the Kaggle Fix 2 T4x2 script with reliable heartbeat output."""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import threading
import time
from pathlib import Path


REPO_DIR = Path(os.environ.get("REPO_DIR", "/kaggle/working/rag-hallucination-detection"))
WRAPPER_LOG = Path("/kaggle/working/fix2_t4x2_wrapper.log")


def count_rows(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return "0"
    try:
        with path.open(newline="") as f:
            return str(max(0, sum(1 for _ in csv.reader(f)) - 1))
    except Exception:
        return "?"


def sum_rows(pattern: str) -> str:
    total = 0
    for path in sorted((REPO_DIR / "data/revision/fix_02").glob(pattern)):
        value = count_rows(path)
        if value.isdigit():
            total += int(value)
    return str(total)


def log(message: str) -> None:
    line = f"[wrapper {time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line, flush=True)
    WRAPPER_LOG.parent.mkdir(parents=True, exist_ok=True)
    with WRAPPER_LOG.open("a") as f:
        f.write(line + "\n")


def status_line() -> str:
    base = REPO_DIR / "data/revision/fix_02"
    return (
        "status "
        f"fix2_final={count_rows(base / 'per_query.csv')} "
        f"fix2_gpu0={count_rows(base / 'per_query_gpu0.csv')} "
        f"fix2_gpu1={count_rows(base / 'per_query_gpu1.csv')} "
        f"fix2_partials={sum_rows('*_partial_gpu*.csv')}"
    )


def stream_reader(proc: subprocess.Popen[str], log_path: Path) -> None:
    assert proc.stdout is not None
    with log_path.open("a") as f:
        for line in proc.stdout:
            print(line, end="", flush=True)
            f.write(line)
            f.flush()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        default="parallel",
        choices=["setup", "parallel", "merge", "repair", "status", "package", "full"],
    )
    parser.add_argument("--heartbeat", type=int, default=30)
    args = parser.parse_args()

    WRAPPER_LOG.write_text("")
    if not REPO_DIR.exists():
        log(f"ERROR: repo dir missing: {REPO_DIR}")
        return 2

    os.chdir(REPO_DIR)
    cmd = ["bash", "scripts/kaggle_fix2_t4x2.sh", args.stage]
    log(f"START stage={args.stage}")
    log("command=" + " ".join(cmd))
    log(status_line())

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    output_log = Path(f"/kaggle/working/fix2_t4x2_{args.stage}.log")
    reader = threading.Thread(target=stream_reader, args=(proc, output_log), daemon=True)
    reader.start()

    start = time.time()
    while proc.poll() is None:
        time.sleep(args.heartbeat)
        elapsed = int(time.time() - start)
        log(f"heartbeat stage={args.stage} elapsed={elapsed}s {status_line()}")

    rc = proc.wait()
    reader.join(timeout=5)
    log(f"END stage={args.stage} rc={rc} elapsed={int(time.time() - start)}s")
    log(status_line())
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
