"""Fuzzing tests for _RE_C_LIKE_BLOCK — ReDoS protection."""

import time

from hypothesis import given, settings
from hypothesis import strategies as st

from arachna.differ_structural import _RE_C_LIKE_BLOCK


@settings(deadline=500)
@given(st.text(max_size=10000))
def test_re_c_like_block_no_backtracking_explosion(text):
    """_RE_C_LIKE_BLOCK.finditer completes under 100ms for any input up to 10KB."""
    start = time.perf_counter()
    list(_RE_C_LIKE_BLOCK.finditer(text))
    elapsed = time.perf_counter() - start
    assert elapsed < 0.1, f"_RE_C_LIKE_BLOCK took {elapsed:.3f}s on input of length {len(text)}"


@settings(deadline=500)
@given(st.text(max_size=1000))
def test_re_c_like_block_no_exception(text):
    """_RE_C_LIKE_BLOCK.finditer never raises an exception."""
    try:
        list(_RE_C_LIKE_BLOCK.finditer(text))
    except Exception as e:
        raise AssertionError(
            f"_RE_C_LIKE_BLOCK raised {type(e).__name__}: {e} on input of length {len(text)}"
        ) from e


def test_re_c_like_block_crafted_nested_braces():
    """Deeply nested braces should not cause exponential backtracking."""
    # Crafted input: many nested {'s without closing
    text = "function foo() {" + "{" * 5000
    start = time.perf_counter()
    list(_RE_C_LIKE_BLOCK.finditer(text))
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"_RE_C_LIKE_BLOCK took {elapsed:.3f}s on nested braces"


def test_re_c_like_block_crafted_alternations():
    """Many partial matches across alternations should not explode."""
    # Crafted input: many keywords that partially match
    text = "func " * 5000
    start = time.perf_counter()
    list(_RE_C_LIKE_BLOCK.finditer(text))
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"_RE_C_LIKE_BLOCK took {elapsed:.3f}s on repeated keywords"
