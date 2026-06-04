"""Extended integration tests for --diff --full CLI (v1.6.2 coverage gaps)."""

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


# TC-064: --diff --full without --from uses HEAD
def test_diff_full_uses_head(tmp_path, monkeypatch):
    """TC-064: --diff --full without explicit --from uses HEAD snapshot."""
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
    # Create snapshot (becomes HEAD)
    _arachna("--snapshot", "--profile", "code", "--name", "head-test", cwd=cwd)

    # Modify file
    (tmp_path / "src" / "main.py").write_text("modified")

    # Run --diff --full without --from (uses HEAD)
    result = _arachna("--diff", "--profile", "code", "--full", cwd=cwd)
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    out_dir = tmp_path / "out"
    files = list(out_dir.glob("chat-diff-full*"))
    assert len(files) >= 1, f"No output files in {out_dir}"
    content = files[0].read_text()
    assert "FULL CONTEXT + DIFF" in content
    assert "Changes since snapshot" in content


# TC-065: --diff --full with --output-dir flag
def test_diff_full_with_output_dir_flag(tmp_path, monkeypatch):
    """TC-065: --diff --full --output-dir writes to custom directory."""
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
    _arachna("--snapshot", "--profile", "code", "--name", "output-dir-test", cwd=cwd)
    (tmp_path / "src" / "main.py").write_text("modified again")

    custom_dir = tmp_path / "custom_diff_output"
    result = _arachna(
        "--diff",
        "--from",
        "output-dir-test",
        "--profile",
        "code",
        "--full",
        "--output-dir",
        str(custom_dir),
        cwd=cwd,
    )
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    # Files in custom dir, not default
    assert custom_dir.is_dir()
    custom_files = list(custom_dir.glob("chat-diff-full*"))
    assert len(custom_files) >= 1

    # Default dir should NOT have chat-diff-full files
    default_out = tmp_path / "out"
    default_files = list(default_out.glob("chat-diff-full*")) if default_out.exists() else []
    assert len(default_files) == 0


# TC-066: --diff --full with --compress flag
def test_diff_full_with_compress(tmp_path, monkeypatch):
    """TC-066: --diff --full --compress collapses blank lines in full context."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("line1\n\n\n\nline2\n")
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
    _arachna("--snapshot", "--profile", "code", "--name", "compress-test", cwd=cwd)
    (tmp_path / "src" / "main.py").write_text("line1\n\n\n\nline2_changed\n")

    result = _arachna(
        "--diff",
        "--from",
        "compress-test",
        "--profile",
        "code",
        "--full",
        "--compress",
        cwd=cwd,
    )
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    out_dir = tmp_path / "out"
    files = list(out_dir.glob("chat-diff-full*"))
    assert len(files) >= 1
    content = files[0].read_text()
    # 4+ blank lines collapsed to 2
    assert "\n\n\n\n" not in content
    assert "FULL CONTEXT + DIFF" in content


# TC-067: --diff --full with no changes
def test_diff_full_no_changes(tmp_path, monkeypatch):
    """TC-067: --diff --full with no changes since snapshot shows no-changes message."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("unchanged content")
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
    _arachna("--snapshot", "--profile", "code", "--name", "no-change-test", cwd=cwd)

    # Don't modify anything
    result = _arachna(
        "--diff",
        "--from",
        "no-change-test",
        "--profile",
        "code",
        "--full",
        cwd=cwd,
    )
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    out_dir = tmp_path / "out"
    files = list(out_dir.glob("chat-diff-full*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "No changes since snapshot" in content
