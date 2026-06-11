"""Shared fixtures for integration tests."""

import os
import subprocess
import sys


def _arachna(*args: str) -> subprocess.CompletedProcess:
    """Run arachna as subprocess, return CompletedProcess."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "arachna", *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
