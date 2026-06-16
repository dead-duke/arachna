"""TC-178: find, env, hg, svn removed from _ALLOWED_COMMANDS."""

from arachna.domain.runner import _ALLOWED_COMMANDS, _validate_command


def test_find_not_in_allowlist():
    """find is no longer in _ALLOWED_COMMANDS."""
    assert "find" not in _ALLOWED_COMMANDS


def test_env_not_in_allowlist():
    """env is no longer in _ALLOWED_COMMANDS."""
    assert "env" not in _ALLOWED_COMMANDS


def test_hg_not_in_allowlist():
    """hg is no longer in _ALLOWED_COMMANDS."""
    assert "hg" not in _ALLOWED_COMMANDS


def test_svn_not_in_allowlist():
    """svn is no longer in _ALLOWED_COMMANDS."""
    assert "svn" not in _ALLOWED_COMMANDS


def test_find_rejected_by_validate():
    """find is blocked by blocked word list."""
    is_safe, reason = _validate_command("find . -name '*.py'")
    assert not is_safe
    assert "blocked pattern" in reason


def test_env_rejected_by_validate():
    """env is rejected — not in allowlist, no shell metachar."""
    is_safe, reason = _validate_command("env")
    assert not is_safe
    assert "not in allowlist" in reason


def test_find_exec_rejected():
    """find -exec is blocked — find is a blocked word."""
    is_safe, reason = _validate_command("find . -name '*.py' -exec cat {} \\;")
    assert not is_safe
