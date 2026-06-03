"""Integration tests for --diff --full CLI (v1.6.2)."""

import json
import os
import subprocess
import sys


def _arachna(*args: str, cwd=None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "arachna", *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        cwd=cwd,
    )


# TC-061: --diff --full creates combined output
def test_diff_full_creates_combined_output(tmp_path, monkeypatch):
    """TC-061: --diff --full creates combined context + diff output.

    Verifies BUG-001 fix: output_dir from .arachna.json is respected.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original")
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 32768,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    cwd = str(tmp_path)
    # Create snapshot
    _arachna("--snapshot", "--profile", "code", "--name", "full-diff-test", cwd=cwd)

    # Modify file
    (tmp_path / "src" / "main.py").write_text("modified")

    # Run --diff --full (no explicit --output-dir — relies on config, BUG-001 fixed)
    result = _arachna("--diff", "--from", "full-diff-test", "--profile", "code", "--full", cwd=cwd)
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    out_dir = tmp_path / "out"
    files = list(out_dir.glob("chat-diff-full*"))
    assert len(files) >= 1, (
        f"No files in {out_dir}, "
        f"contents: {list(out_dir.iterdir()) if out_dir.exists() else 'dir not found'}"
    )
    content = files[0].read_text()
    assert "FULL CONTEXT + DIFF" in content
    assert "main.py" in content
    assert "Changes since snapshot" in content


# TC-062: --diff --full with no snapshot exits 1
def test_diff_full_no_snapshot(tmp_path, monkeypatch):
    """TC-062: --diff --full without snapshots exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 32768,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    result = _arachna("--diff", "--profile", "code", "--full", cwd=str(tmp_path))
    assert result.returncode == 1
    assert "No snapshots found" in result.stdout
