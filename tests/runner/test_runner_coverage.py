"""Additional coverage for runner.py gaps: dry-run + interactive, audit log edge cases."""

import json
import subprocess
from unittest.mock import patch

from arachna.runner import (
    _get_audit_log_path,
    _is_safe_command,
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


# ── _validate_command with allow_dangerous + blocked phrases ──────


def test_validate_command_allow_dangerous_blocked_phrase():
    """allow_dangerous=True bypasses blocked phrases (rm -rf /)."""
    from arachna.runner import _validate_command

    is_safe, reason = _validate_command("rm -rf /", allow_dangerous=True)
    assert is_safe


def test_validate_command_allow_dangerous_unknown_command():
    """allow_dangerous=True bypasses allowlist check."""
    from arachna.runner import _validate_command

    is_safe, reason = _validate_command("unknown_cmd_xyz arg", allow_dangerous=True)
    assert is_safe


def test_validate_command_allow_dangerous_pipe_unknown():
    """allow_dangerous=True bypasses pipe part allowlist check."""
    from arachna.runner import _validate_command

    is_safe, reason = _validate_command("echo hello | unknown_cmd", allow_dangerous=True)
    assert is_safe


# ── run_command with allow_dangerous ───────────────────────────────


def test_run_command_allow_dangerous_curl():
    """curl is blocked by default, but allow_dangerous=True executes it."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="output\n")
        result = run_command("curl http://example.com", allow_dangerous=True)
        assert result == "output\n"


def test_run_command_allow_dangerous_rm():
    """rm -rf is blocked phrase, but allow_dangerous=True bypasses."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="")
        result = run_command("rm -rf /", allow_dangerous=True)
        assert result == ""


# ── _log_command error handling ────────────────────────────────────


def test_log_command_os_error_on_mkdir_parents(tmp_path, monkeypatch):
    """_log_command handles OSError when creating parent directories fails."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    # Make 'out' a file, so out/.arachna_commands.log mkdir fails
    (tmp_path / "out").write_text("blocked")

    # Should not raise
    _log_command("echo hello", True)


def test_log_command_os_error_on_write(tmp_path, monkeypatch):
    """_log_command handles OSError when writing to log file."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    # Make log file a directory — write will fail
    log_file = out_dir / ".arachna_commands.log"
    log_file.mkdir()

    # Should not raise
    _log_command("echo hello", True)


def test_log_command_none_log_path(monkeypatch):
    """_log_command handles _get_audit_log_path returning None."""
    with patch("arachna.runner._get_audit_log_path", return_value=None):
        # Should not raise
        _log_command("echo hello", True)


# ── Dry-run + interactive combined paths ───────────────────────────


def test_run_command_empty_after_strip():
    """Whitespace-only command returns empty."""
    assert run_command("   ") == ""


def test_run_command_os_error_on_execution():
    """OSError during subprocess.run returns empty."""
    with patch("subprocess.run", side_effect=OSError("bad interpreter")):
        result = run_command("some_broken_cmd")
        assert result == ""


def test_run_command_value_error_on_execution():
    """ValueError during subprocess.run returns empty."""
    with patch("subprocess.run", side_effect=ValueError("invalid argument")):
        result = run_command("some_cmd")
        assert result == ""


def test_is_safe_command_unknown():
    """_is_safe_command returns False for commands not in allowlist."""
    assert not _is_safe_command("python3 script.py")
    assert not _is_safe_command("node server.js")
    assert not _is_safe_command("")


def test_is_safe_command_with_shell_chars():
    """_is_safe_command returns False for commands with shell metacharacters."""
    assert not _is_safe_command("echo hello | cat")
    assert not _is_safe_command("echo hello > file.txt")
    assert not _is_safe_command("echo hello && echo world")


# ── run_command with shell metacharacters (shell=True path) ────────


def test_run_command_shell_double_ampersand():
    """Shell=True path with && works."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="a\nb\n")
        result = run_command("echo a && echo b")
        assert result == "a\nb\n"


def test_run_command_shell_redirect():
    """Shell=True path with > works."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="")
        result = run_command("echo hello > /dev/null")
        assert result == ""


# ── _get_audit_log_path edge cases ─────────────────────────────────


def test_get_audit_log_path_exception_fallback(tmp_path, monkeypatch):
    """_get_audit_log_path returns cwd fallback on unexpected exception."""
    monkeypatch.chdir(tmp_path)
    # Corrupted JSON that raises on read_text
    (tmp_path / ".arachna.json").write_text("{invalid")

    log_path = _get_audit_log_path()
    assert log_path is not None
    assert log_path.name == ".arachna_commands.log"


def test_get_audit_log_path_parent_cwd_exception(monkeypatch):
    """_get_audit_log_path handles exception from Path.cwd()."""
    with patch("pathlib.Path.cwd", side_effect=OSError("no cwd")):
        log_path = _get_audit_log_path()
        assert log_path is None
