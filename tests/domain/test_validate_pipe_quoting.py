"""Tests for BUG-001: _validate_command splits pipe without respect for quotes.

BUG-001 fixed in v1.3.0 — pipe splitting now respects shell quoting.
"""

from arachna.domain.runner import _validate_command


def test_pipe_inside_single_quotes_safe():
    """Pipe inside single quotes should not be treated as pipe separator."""
    is_safe, reason = _validate_command("tree -I '*.pyc|*.egg-info' src", allow_file_args=True)
    assert is_safe, f"Expected safe, got: {reason}"


def test_pipe_inside_double_quotes_safe():
    """Pipe inside double quotes should not be treated as pipe separator."""
    is_safe, reason = _validate_command('grep "error|warning" log.txt', allow_file_args=True)
    assert is_safe, f"Expected safe, got: {reason}"


def test_or_operator_with_dev_null():
    """|| and 2>/dev/null should be handled as shell metacharacters."""
    is_safe, reason = _validate_command(
        "tree -I '__pycache__|*.pyc|*.egg-info|venv|node_modules' src 2>/dev/null || true",
        allow_file_args=True,
    )
    assert is_safe, f"Expected safe, got: {reason}"


def test_git_log_with_format_containing_pipe():
    """Git log format string may contain | and %n but no blocked patterns as words."""
    cmd = (
        "git log --reverse "
        "--format='=== COMMIT: %h ===%nTITLE: %s%n%nMESSAGE:%n%b%n%nCHANGES:%n' "
        "--stat"
    )
    is_safe, reason = _validate_command(cmd, allow_file_args=True)
    assert is_safe, f"Expected safe, got: {reason}"


def test_actual_pipe_still_detected():
    """Real pipe (outside quotes) should still be validated per-part."""
    is_safe, reason = _validate_command("cat file.txt | grep pattern", allow_file_args=True)
    assert is_safe, f"Expected safe, got: {reason}"


def test_actual_pipe_with_unknown_command():
    """Real pipe with unknown command should be blocked."""
    is_safe, reason = _validate_command("cat file.txt | unknown_cmd_xyz", allow_file_args=True)
    assert not is_safe
    assert "not in allowlist" in reason
