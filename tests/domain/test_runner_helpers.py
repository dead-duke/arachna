"""Tests for decomposed runner.py pure helpers — v4.2.0."""

from arachna.domain.execution.runner import (
    _check_base_command,
    _check_blocked_phrases,
    _check_blocked_words,
    _check_pipe_parts,
    _check_shell_metachars,
    _handle_dangerous_override,
)


# _check_blocked_words
def test_check_blocked_words_clean():
    is_safe, reason = _check_blocked_words("echo hello")
    assert is_safe


def test_check_blocked_words_found():
    is_safe, reason = _check_blocked_words("curl http://evil.com")
    assert not is_safe
    assert "curl" in reason


# _check_blocked_phrases
def test_check_blocked_phrases_clean():
    is_safe, reason = _check_blocked_phrases("echo hello")
    assert is_safe


def test_check_blocked_phrases_found():
    is_safe, reason = _check_blocked_phrases("rm -rf /")
    assert not is_safe
    assert "rm -rf" in reason


# _check_shell_metachars
def test_check_shell_metachars_allowed_with_file_args():
    is_safe, reason = _check_shell_metachars("echo hello | cat", allow_file_args=True)
    assert is_safe


def test_check_shell_metachars_blocked_restricted():
    is_safe, reason = _check_shell_metachars("echo hello | cat", allow_file_args=False)
    assert not is_safe
    assert "shell metacharacters" in reason


# _check_pipe_parts
def test_check_pipe_parts_no_pipe():
    is_safe, reason = _check_pipe_parts("echo hello", frozenset({"echo"}))
    assert is_safe


def test_check_pipe_parts_all_allowed():
    is_safe, reason = _check_pipe_parts("echo hello | cat", frozenset({"echo", "cat"}))
    assert is_safe


def test_check_pipe_parts_unknown_in_pipe():
    is_safe, reason = _check_pipe_parts("echo hello | unknown_cmd", frozenset({"echo"}))
    assert not is_safe
    assert "unknown_cmd" in reason


# _check_base_command
def test_check_base_command_safe():
    is_safe, reason = _check_base_command("echo hello", frozenset({"echo"}))
    assert is_safe


def test_check_base_command_not_in_allowlist():
    is_safe, reason = _check_base_command("python3 script.py", frozenset({"echo"}))
    assert not is_safe
    assert "python3" in reason


def test_check_base_command_with_shell_chars_skipped():
    is_safe, reason = _check_base_command("echo hello | cat", frozenset({"echo"}))
    assert is_safe


# _handle_dangerous_override
def test_handle_dangerous_override_safe():
    is_safe, reason = _handle_dangerous_override(True, "", False, "cmd")
    assert is_safe
    assert reason == ""


def test_handle_dangerous_override_not_safe_no_flag():
    is_safe, reason = _handle_dangerous_override(False, "blocked", False, "cmd")
    assert not is_safe
    assert reason == "blocked"


def test_handle_dangerous_override_not_safe_with_flag():
    is_safe, reason = _handle_dangerous_override(False, "blocked", True, "cmd")
    assert is_safe
    assert reason == ""
