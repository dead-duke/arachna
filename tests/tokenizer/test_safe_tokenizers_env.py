"""Tests for ARACHNA_SAFE_TOKENIZERS env var."""

from arachna.tokenizer import _is_safe_tokenizer


def test_known_safe_tokenizers():
    """tiktoken and transformers are in default safe list."""
    assert _is_safe_tokenizer("tiktoken:cl100k_base")
    assert _is_safe_tokenizer("transformers:gpt2")


def test_unknown_tokenizer_blocked():
    """Unknown tokenizer not in safe list is blocked."""
    assert not _is_safe_tokenizer("mistral:tokenizer")


def test_default_always_safe():
    """'default' is always safe regardless of env."""
    assert _is_safe_tokenizer("default")
    assert _is_safe_tokenizer("")
