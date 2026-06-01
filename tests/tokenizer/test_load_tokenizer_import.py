"""Tests for load_tokenizer import paths."""

import sys

import pytest

from arachna.tokenizer import _is_safe_tokenizer, load_tokenizer


def test_load_tokenizer_unsafe_module_raises_value_error():
    """load_tokenizer raises ValueError for modules that fail _is_safe_tokenizer."""
    assert not _is_safe_tokenizer("nonexistent_module_xyz")
    with pytest.raises(ValueError, match="Unsafe tokenizer"):
        load_tokenizer("nonexistent_module_xyz:count_tokens")


def test_load_tokenizer_local_file_not_in_sys_path(tmp_path, monkeypatch):
    """load_tokenizer raises ModuleNotFoundError when local file exists but not in sys.path."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "my_tok.py").write_text("def count_tokens(t): return 1")

    assert _is_safe_tokenizer("my_tok")
    # Module is safe but not importable — cwd not in sys.path in test
    with pytest.raises(ModuleNotFoundError):
        load_tokenizer("my_tok:nonexistent_function")


def test_load_tokenizer_attribute_error(tmp_path, monkeypatch):
    """load_tokenizer raises AttributeError when function doesn't exist in module."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "my_tok3.py").write_text("def count_tokens(t): return 1")
    sys.path.insert(0, str(tmp_path))
    try:
        with pytest.raises(AttributeError):
            load_tokenizer("my_tok3:nonexistent_function")
    finally:
        sys.path.pop(0)
        import importlib

        importlib.invalidate_caches()
        if "my_tok3" in sys.modules:
            del sys.modules["my_tok3"]
