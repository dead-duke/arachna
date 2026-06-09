"""Property-based tests for _split_pipe_parts."""

from hypothesis import given
from hypothesis import strategies as st

from arachna.runner import _split_pipe_parts


@given(st.text())
def test_split_pipe_parts_always_returns_list(text):
    """_split_pipe_parts always returns a non-empty list."""
    parts = _split_pipe_parts(text)
    assert isinstance(parts, list)
    assert len(parts) >= 1


@given(st.text(min_size=1))
def test_split_pipe_parts_without_pipe_returns_one_part(text):
    """Text without | returns single part."""
    if "|" not in text:
        parts = _split_pipe_parts(text)
        assert len(parts) == 1
