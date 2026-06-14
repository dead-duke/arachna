"""Shared fixtures for integration tests."""

import os
import subprocess
import sys
from pathlib import Path


def _arachna(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run arachna as subprocess, return CompletedProcess.

    Args:
        *args: CLI arguments to pass to arachna.
        cwd: Working directory for the subprocess. MUST be provided
             to avoid inheriting a stale cwd from monkeypatch.chdir.
    """
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
