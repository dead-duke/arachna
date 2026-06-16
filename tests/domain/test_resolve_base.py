"""Tests for _resolve_base edge cases in runner.py."""

from arachna.domain.runner import _resolve_base


def test_resolve_base_value_error():
    """_resolve_base returns empty string on ValueError from shlex.split."""
    # Unclosed quote causes ValueError in shlex
    assert _resolve_base("echo 'hello") == ""


def test_resolve_base_empty_after_strip():
    """_resolve_base returns empty string for whitespace-only input."""
    assert _resolve_base("   ") == ""
