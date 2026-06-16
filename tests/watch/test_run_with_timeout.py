"""Tests for _run_with_timeout in differ_structural.py."""

import time

import pytest

from arachna.domain.language_dispatch import RegexTimeoutError, _run_with_timeout


def test_run_with_timeout_completes_fast():
    """Fast function completes within timeout and returns result."""
    result = _run_with_timeout(lambda: 42, timeout=1.0)
    assert result == 42


def test_run_with_timeout_passes_exception():
    """Function that raises passes exception through."""
    with pytest.raises(ValueError, match="test error"):
        _run_with_timeout(lambda: (_ for _ in ()).throw(ValueError("test error")), timeout=1.0)


def test_run_with_timeout_slow_function_raises_timeout():
    """Slow function that exceeds timeout raises RegexTimeoutError."""

    def slow():
        time.sleep(0.2)
        return "done"

    with pytest.raises(RegexTimeoutError, match="timed out"):
        _run_with_timeout(slow, timeout=0.05)


def test_run_with_timeout_exact_boundary():
    """Function just under timeout completes successfully."""
    result = _run_with_timeout(lambda: "ok", timeout=1.0)
    assert result == "ok"


def test_run_with_timeout_none_return():
    """Function that returns None works."""
    result = _run_with_timeout(lambda: None, timeout=1.0)
    assert result is None
