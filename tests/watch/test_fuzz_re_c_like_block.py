"""Fuzzing tests for _BLOCK_PATTERNS — ReDoS protection."""

import time

from hypothesis import given, settings
from hypothesis import strategies as st

from arachna.domain.language_dispatch import _BLOCK_PATTERNS


@settings(deadline=500)
@given(st.text(max_size=10000))
def test_block_patterns_no_backtracking_explosion(text):
    """Each pattern in _BLOCK_PATTERNS completes under 100ms for any input up to 10KB."""
    for (pattern,) in _BLOCK_PATTERNS:
        start = time.perf_counter()
        list(pattern.finditer(text))
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, (
            f"Pattern {pattern.pattern[:60]} took {elapsed:.3f}s on input of length {len(text)}"
        )


@settings(deadline=500)
@given(st.text(max_size=1000))
def test_block_patterns_no_exception(text):
    """No pattern raises an exception on any input."""
    for (pattern,) in _BLOCK_PATTERNS:
        try:
            list(pattern.finditer(text))
        except Exception as e:
            raise AssertionError(
                f"Pattern {pattern.pattern[:60]} raised {type(e).__name__}: {e} on input of length {len(text)}"
            ) from e


def test_block_patterns_crafted_nested_braces():
    """Deeply nested braces should not cause exponential backtracking."""
    text = "function foo() {" + "{" * 5000
    for (pattern,) in _BLOCK_PATTERNS:
        start = time.perf_counter()
        list(pattern.finditer(text))
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Pattern {pattern.pattern[:60]} took {elapsed:.3f}s on nested braces"


def test_block_patterns_crafted_alternations():
    """Many partial matches across patterns should not explode."""
    text = "func " * 5000
    for (pattern,) in _BLOCK_PATTERNS:
        start = time.perf_counter()
        list(pattern.finditer(text))
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, (
            f"Pattern {pattern.pattern[:60]} took {elapsed:.3f}s on repeated keywords"
        )
