"""Shared fixtures for integration tests."""

import os
import subprocess
import sys
from pathlib import Path


def _arachna(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "arachna", *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        cwd=str(cwd) if cwd else None,
    )
