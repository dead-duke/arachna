"""Tests for _load_tiktoken and _load_transformers — with real packages installed."""

from arachna.tokenizer import load_tokenizer


def test_load_tiktoken_real():
    """_load_tiktoken with real tiktoken installed."""
    tok = load_tokenizer("tiktoken")
    result = tok("hello world")
    assert isinstance(result, int)
    assert result > 0


def test_load_tiktoken_custom_encoding():
    """_load_tiktoken with custom encoding."""
    tok = load_tokenizer("tiktoken:cl100k_base")
    result = tok("hello world")
    assert isinstance(result, int)
    assert result > 0


def test_load_transformers_real():
    """_load_transformers with real transformers installed."""
    tok = load_tokenizer("transformers")
    result = tok("hello world")
    assert isinstance(result, int)
    assert result > 0
