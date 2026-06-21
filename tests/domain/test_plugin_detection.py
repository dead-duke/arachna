"""Tests for plugin detection — works with or without real tiktoken/transformers."""

import pytest

from arachna.domain.tokenization.tokenizer import _has_tiktoken, _has_transformers, load_tokenizer

_HAS_TIKTOKEN = _has_tiktoken()
_HAS_TRANSFORMERS = _has_transformers()


def test_check_tokenizer_plugins_detection():
    if _HAS_TIKTOKEN:
        assert _has_tiktoken()
    if _HAS_TRANSFORMERS:
        assert _has_transformers()


def test_load_tokenizer_tiktoken_fallback():
    if _HAS_TIKTOKEN:
        pytest.skip("tiktoken is installed — fallback not testable")
    with pytest.raises(ValueError, match="tiktoken is not installed"):
        load_tokenizer("tiktoken:cl100k_base")


def test_load_tokenizer_transformers_fallback():
    if _HAS_TRANSFORMERS:
        pytest.skip("transformers is installed — fallback not testable")
    with pytest.raises(ValueError, match="transformers is not installed"):
        load_tokenizer("transformers:gpt2")


@pytest.mark.skipif(not _HAS_TIKTOKEN, reason="tiktoken not installed")
def test_load_tokenizer_tiktoken_real():
    tok = load_tokenizer("tiktoken")
    result = tok("hello world")
    assert isinstance(result, int)
    assert result > 0


@pytest.mark.skipif(not _HAS_TIKTOKEN, reason="tiktoken not installed")
def test_load_tokenizer_tiktoken_custom_encoding():
    tok = load_tokenizer("tiktoken:cl100k_base")
    result = tok("hello world")
    assert isinstance(result, int)
    assert result > 0


@pytest.mark.skipif(not _HAS_TRANSFORMERS, reason="transformers not installed")
def test_load_tokenizer_transformers_real():
    tok = load_tokenizer("transformers")
    result = tok("hello world")
    assert isinstance(result, int)
    assert result > 0
