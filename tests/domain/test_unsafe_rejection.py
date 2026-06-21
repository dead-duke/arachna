"""Tests for tokenizer safety — unsafe modules must raise ValueError."""

import pytest

from arachna.domain.tokenization.tokenizer import _is_safe_tokenizer, load_tokenizer


def test_is_safe_tokenizer_blocks_os():
    assert not _is_safe_tokenizer("os:system")


def test_is_safe_tokenizer_blocks_subprocess():
    assert not _is_safe_tokenizer("subprocess:check_output")


def test_is_safe_tokenizer_blocks_sys():
    assert not _is_safe_tokenizer("sys")


def test_is_safe_tokenizer_blocks_builtins():
    assert not _is_safe_tokenizer("builtins:eval")


def test_is_safe_tokenizer_blocks_importlib():
    assert not _is_safe_tokenizer("importlib:import_module")


def test_is_safe_tokenizer_blocks_requests():
    assert not _is_safe_tokenizer("requests:get")


def test_is_safe_tokenizer_allows_default():
    assert _is_safe_tokenizer("default")
    assert _is_safe_tokenizer("")


def test_load_tokenizer_raises_value_error_for_os():
    with pytest.raises(ValueError, match="Unsafe tokenizer"):
        load_tokenizer("os:system")


def test_load_tokenizer_raises_value_error_for_subprocess():
    with pytest.raises(ValueError, match="Unsafe tokenizer"):
        load_tokenizer("subprocess:check_output")


def test_load_tokenizer_raises_value_error_for_sys():
    with pytest.raises(ValueError, match="Unsafe tokenizer"):
        load_tokenizer("sys:exit")


def test_load_tokenizer_raises_value_error_for_shutil():
    with pytest.raises(ValueError, match="Unsafe tokenizer"):
        load_tokenizer("shutil:rmtree")


def test_load_tokenizer_allows_tiktoken():
    assert _is_safe_tokenizer("tiktoken:cl100k_base")
