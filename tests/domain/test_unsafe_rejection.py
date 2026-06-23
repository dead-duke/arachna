"""Tests for tokenizer safety — unsafe modules must raise ValueError."""

from pathlib import Path

import pytest

from arachna.domain.tokenization.tokenizer import _is_safe_tokenizer, load_tokenizer


def test_is_safe_tokenizer_blocks_os():
    assert not _is_safe_tokenizer("os:system", root=Path.cwd())


def test_is_safe_tokenizer_blocks_subprocess():
    assert not _is_safe_tokenizer("subprocess:check_output", root=Path.cwd())


def test_is_safe_tokenizer_blocks_sys():
    assert not _is_safe_tokenizer("sys", root=Path.cwd())


def test_is_safe_tokenizer_blocks_builtins():
    assert not _is_safe_tokenizer("builtins:eval", root=Path.cwd())


def test_is_safe_tokenizer_blocks_importlib():
    assert not _is_safe_tokenizer("importlib:import_module", root=Path.cwd())


def test_is_safe_tokenizer_blocks_requests():
    assert not _is_safe_tokenizer("requests:get", root=Path.cwd())


def test_is_safe_tokenizer_allows_default():
    assert _is_safe_tokenizer("default", root=Path.cwd())
    assert _is_safe_tokenizer("", root=Path.cwd())


def test_load_tokenizer_raises_value_error_for_os():
    with pytest.raises(ValueError, match="Unsafe tokenizer"):
        load_tokenizer("os:system", root=Path.cwd())


def test_load_tokenizer_raises_value_error_for_subprocess():
    with pytest.raises(ValueError, match="Unsafe tokenizer"):
        load_tokenizer("subprocess:check_output", root=Path.cwd())


def test_load_tokenizer_raises_value_error_for_sys():
    with pytest.raises(ValueError, match="Unsafe tokenizer"):
        load_tokenizer("sys:exit", root=Path.cwd())


def test_load_tokenizer_raises_value_error_for_shutil():
    with pytest.raises(ValueError, match="Unsafe tokenizer"):
        load_tokenizer("shutil:rmtree", root=Path.cwd())


def test_load_tokenizer_allows_tiktoken():
    assert _is_safe_tokenizer("tiktoken:cl100k_base", root=Path.cwd())
