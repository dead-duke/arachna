"""Tests for uncovered branches in runner.py."""

import subprocess
from unittest.mock import patch

from arachna.runner import (
    _get_audit_log_path,
    _log_command,
    run_command,
)


def _completed_process(stdout="", stderr="", returncode=0, args=None):
    return subprocess.CompletedProcess(
        args=args or ["echo", "hello"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_dry_run_unsafe_non_interactive():
    """Unsafe command in dry-run non-interactive returns empty."""
    result = run_command("curl http://evil.com", dry_run=True)
    assert result == ""


def test_dry_run_unsafe_interactive_no():
    """Dry-run unsafe interactive: user declines, returns empty."""
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("curl http://evil.com", dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_shell_metachar_non_interactive():
    """Command with shell metachar (not in allowlist) in dry-run non-interactive."""
    result = run_command("echo hello > /tmp/out", dry_run=True)
    assert result == ""


def test_dry_run_shell_metachar_interactive_no():
    """Dry-run shell metachar interactive: user declines."""
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("echo hello > /tmp/out", dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_shell_metachar_interactive_yes():
    """Dry-run shell metachar interactive: user confirms, executes."""
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="y"),
    ):
        mock_run.return_value = _completed_process(stdout="hello\n")
        result = run_command("echo hello > /tmp/out", dry_run=True, interactive=True)
        assert result == "hello\n"


def test_log_command_no_config(tmp_path, monkeypatch):
    """_get_audit_log_path returns fallback when no .arachna.json."""
    monkeypatch.chdir(tmp_path)
    log_path = _get_audit_log_path()
    assert log_path is not None
    assert log_path.name == ".arachna_commands.log"


def test_log_command_os_error_on_write(tmp_path, monkeypatch):
    """_log_command handles OSError when writing audit log."""
    import json

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    # Make the log file a directory to cause OSError on write
    (out_dir / ".arachna_commands.log").mkdir()

    # Should not raise
    _log_command("echo hello", True)


def test_log_command_permission_error_on_mkdir(tmp_path, monkeypatch):
    """_log_command handles OSError when mkdir fails."""
    import json

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    # Make 'out' a file instead of directory — mkdir will fail
    (tmp_path / "out").write_text("blocked")

    # Should not raise
    _log_command("echo hello", True)
