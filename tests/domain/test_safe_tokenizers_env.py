"""Tests for ARACHNA_SAFE_TOKENIZERS env var."""

from arachna.domain.tokenization.tokenizer import _is_safe_tokenizer


def test_known_safe_tokenizers():
    assert _is_safe_tokenizer("tiktoken:cl100k_base")
    assert _is_safe_tokenizer("transformers:gpt2")


def test_unknown_tokenizer_blocked():
    assert not _is_safe_tokenizer("mistral:tokenizer")


def test_default_always_safe():
    assert _is_safe_tokenizer("default")
    assert _is_safe_tokenizer("")
