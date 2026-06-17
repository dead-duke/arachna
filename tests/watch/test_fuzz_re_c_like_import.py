"""Fuzzing tests for _C_LIKE_IMPORT_PATTERNS — ReDoS protection."""

import time

from hypothesis import given, settings
from hypothesis import strategies as st

from arachna.domain.formatter import _C_LIKE_IMPORT_PATTERNS


@settings(deadline=500)
@given(st.text(max_size=10000))
def test_re_c_like_import_no_backtracking_explosion(text):
    """Each pattern in _C_LIKE_IMPORT_PATTERNS completes under 100ms for any input up to 10KB."""
    for pattern in _C_LIKE_IMPORT_PATTERNS:
        start = time.perf_counter()
        list(pattern.finditer(text))
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, (
            f"Pattern {pattern.pattern[:60]} took {elapsed:.3f}s on input of length {len(text)}"
        )


@settings(deadline=500)
@given(st.text(max_size=1000))
def test_re_c_like_import_no_exception(text):
    """_C_LIKE_IMPORT_PATTERNS never raise an exception."""
    for pattern in _C_LIKE_IMPORT_PATTERNS:
        try:
            list(pattern.finditer(text))
        except Exception as e:
            raise AssertionError(
                f"Pattern {pattern.pattern[:60]} raised {type(e).__name__}: {e} on input of length {len(text)}"
            ) from e


def test_re_c_like_import_crafted_long_strings():
    """Very long string literals should not cause backtracking."""
    text = "import " + '"' + "x" * 5000 + '"'
    for pattern in _C_LIKE_IMPORT_PATTERNS:
        start = time.perf_counter()
        list(pattern.finditer(text))
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Pattern took {elapsed:.3f}s on long string"


def test_re_c_like_import_crafted_many_quotes():
    """Many quote characters should not explode."""
    text = "import " + "'\"'\"'" * 2000
    for pattern in _C_LIKE_IMPORT_PATTERNS:
        start = time.perf_counter()
        list(pattern.finditer(text))
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Pattern took {elapsed:.3f}s on many quotes"
