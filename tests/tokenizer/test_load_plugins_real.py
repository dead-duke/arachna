"""Tests for _load_tiktoken and _load_transformers — with real packages installed."""

import pytest

from arachna.domain.tokenizer import _has_tiktoken, _has_transformers, load_tokenizer


@pytest.mark.skipif(not _has_tiktoken(), reason="tiktoken not installed")
def test_load_tiktoken_real():
    tok = load_tokenizer("tiktoken")
    result = tok("hello world")
    assert isinstance(result, int)
    assert result > 0


@pytest.mark.skipif(not _has_tiktoken(), reason="tiktoken not installed")
def test_load_tiktoken_custom_encoding():
    tok = load_tokenizer("tiktoken:cl100k_base")
    result = tok("hello world")
    assert isinstance(result, int)
    assert result > 0


@pytest.mark.skipif(not _has_transformers(), reason="transformers not installed")
def test_load_transformers_real():
    tok = load_tokenizer("transformers")
    result = tok("hello world")
    assert isinstance(result, int)
    assert result > 0
