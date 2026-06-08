"""Tests for uncovered branches in runner.py."""

import json
import subprocess
from unittest.mock import patch

from arachna.runner import (
    _get_audit_log_path,
    _is_safe_command,
    _log_command,
    _validate_command,
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
    result = run_command("curl http://evil.com", dry_run=True)
    assert result == ""


def test_dry_run_unsafe_interactive_no():
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("curl http://evil.com", dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_shell_metachar_non_interactive():
    result = run_command("echo hello > /tmp/out", dry_run=True)
    assert result == ""


def test_dry_run_shell_metachar_interactive_no():
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("echo hello > /tmp/out", dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_shell_metachar_interactive_yes():
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="y"),
    ):
        mock_run.return_value = _completed_process(stdout="hello\n")
        result = run_command("echo hello > /tmp/out", dry_run=True, interactive=True)
        assert result == "hello\n"


def test_log_command_no_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_path = _get_audit_log_path()
    assert log_path is not None
    assert log_path.name == ".arachna_commands.log"


def test_log_command_os_error_on_write(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / ".arachna_commands.log").mkdir()

    _log_command("echo hello", True)


def test_log_command_permission_error_on_mkdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    (tmp_path / "out").write_text("blocked")

    _log_command("echo hello", True)


def test_validate_command_allow_dangerous_blocked_phrase():
    is_safe, reason = _validate_command("rm -rf /", allow_dangerous=True)
    assert is_safe


def test_validate_command_allow_dangerous_unknown_command():
    is_safe, reason = _validate_command("unknown_cmd_xyz arg", allow_dangerous=True)
    assert is_safe


def test_validate_command_allow_dangerous_pipe_unknown():
    is_safe, reason = _validate_command("echo hello | unknown_cmd", allow_dangerous=True)
    assert is_safe


def test_run_command_allow_dangerous_curl():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="output\n")
        result = run_command("curl http://example.com", allow_dangerous=True)
        assert result == "output\n"


def test_run_command_allow_dangerous_rm():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="")
        result = run_command("rm -rf /", allow_dangerous=True)
        assert result == ""


def test_log_command_os_error_on_mkdir_parents(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    (tmp_path / "out").write_text("blocked")

    _log_command("echo hello", True)


def test_log_command_none_log_path(monkeypatch):
    with patch("arachna.runner._get_audit_log_path", return_value=None):
        _log_command("echo hello", True)


def test_run_command_empty_after_strip():
    assert run_command("   ") == ""


def test_run_command_os_error_on_execution():
    with patch("subprocess.run", side_effect=OSError("bad interpreter")):
        result = run_command("some_broken_cmd")
        assert result == ""


def test_run_command_value_error_on_execution():
    with patch("subprocess.run", side_effect=ValueError("invalid argument")):
        result = run_command("some_cmd")
        assert result == ""


def test_is_safe_command_unknown():
    assert not _is_safe_command("python3 script.py")
    assert not _is_safe_command("node server.js")
    assert not _is_safe_command("")


def test_is_safe_command_with_shell_chars():
    assert not _is_safe_command("echo hello | cat")
    assert not _is_safe_command("echo hello > file.txt")
    assert not _is_safe_command("echo hello && echo world")


def test_run_command_shell_double_ampersand():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="a\nb\n")
        result = run_command("echo a && echo b", allow_file_args=True)
        assert result == "a\nb\n"


def test_run_command_shell_redirect():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="")
        result = run_command("echo hello > /dev/null", allow_file_args=True)
        assert result == ""


def test_get_audit_log_path_exception_fallback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text("{invalid")

    log_path = _get_audit_log_path()
    assert log_path is not None
    assert log_path.name == ".arachna_commands.log"


def test_get_audit_log_path_parent_cwd_exception(monkeypatch):
    with patch("pathlib.Path.cwd", side_effect=OSError("no cwd")):
        log_path = _get_audit_log_path()
        assert log_path is None
