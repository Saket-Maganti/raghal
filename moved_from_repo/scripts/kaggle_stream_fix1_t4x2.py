#!/usr/bin/env python3
"""Stream the T4x2 Fix 1 runner line-by-line in Kaggle.

Kaggle sometimes buffers %%bash output. Running this Python wrapper usually
flushes subprocess output more reliably in the notebook UI.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


REPO_DIR = Path("/kaggle/working/rag-hallucination-detection")
LOG_PATH = Path("/kaggle/working/fix1_stream_wrapper.log")


def log(msg: str) -> None:
    line = f"[stream {time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")


def main() -> int:
    LOG_PATH.write_text("")
    log("starting Fix 1 T4x2 streamed run")
    log(f"repo={REPO_DIR}")
    if not REPO_DIR.exists():
        log("ERROR: repo dir missing; clone repo before running this wrapper")
        return 2

    os.chdir(REPO_DIR)
    cmd = ["bash", "-x", "scripts/kaggle_fix1_parallel_t4x2.sh"]
    log("command=" + " ".join(cmd))

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
    assert proc.stdout is not None
    last = time.time()
    for line in proc.stdout:
        print(line, end="", flush=True)
        with LOG_PATH.open("a") as f:
            f.write(line)
        last = time.time()

    while proc.poll() is None:
        if time.time() - last > 30:
            log("heartbeat: subprocess alive, waiting for output")
            last = time.time()
        time.sleep(1)

    rc = proc.wait()
    log(f"finished rc={rc}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

