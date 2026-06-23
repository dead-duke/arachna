"""Tests for ARACHNA_SAFE_TOKENIZERS env var."""

from pathlib import Path

from arachna.domain.tokenization.tokenizer import _is_safe_tokenizer


def test_known_safe_tokenizers():
    assert _is_safe_tokenizer("tiktoken:cl100k_base", root=Path.cwd())
    assert _is_safe_tokenizer("transformers:gpt2", root=Path.cwd())


def test_unknown_tokenizer_blocked():
    assert not _is_safe_tokenizer("mistral:tokenizer", root=Path.cwd())


def test_default_always_safe():
    assert _is_safe_tokenizer("default", root=Path.cwd())
    assert _is_safe_tokenizer("", root=Path.cwd())
