"""Tests for ARACHNA_SAFE_TOKENIZERS env var (v2.8.2)."""

import os

import pytest


@pytest.fixture(autouse=True)
def _restore_safe_tokenizers():
    """Restore _SAFE_TOKENIZERS after each test to prevent leakage."""
    import arachna.tokenizer as tok_module

    original = tok_module._SAFE_TOKENIZERS
    yield
    tok_module._SAFE_TOKENIZERS = original


def test_custom_safe_tokenizer_via_env(monkeypatch):
    """Custom tokenizer in ARACHNA_SAFE_TOKENIZERS is allowed."""
    import arachna.tokenizer as tok_module

    monkeypatch.setenv("ARACHNA_SAFE_TOKENIZERS", "tiktoken,transformers,mistral")
    tok_module._SAFE_TOKENIZERS = frozenset(
        os.environ.get("ARACHNA_SAFE_TOKENIZERS", "tiktoken,transformers").split(",")
    )

    assert tok_module._is_safe_tokenizer("mistral:tokenizer")
    assert tok_module._is_safe_tokenizer("tiktoken")
    assert tok_module._is_safe_tokenizer("transformers")


def test_unknown_tokenizer_still_blocked(monkeypatch):
    """Unknown tokenizer not in env var is still blocked."""
    import arachna.tokenizer as tok_module

    monkeypatch.setenv("ARACHNA_SAFE_TOKENIZERS", "tiktoken")
    tok_module._SAFE_TOKENIZERS = frozenset(
        os.environ.get("ARACHNA_SAFE_TOKENIZERS", "tiktoken,transformers").split(",")
    )

    assert not tok_module._is_safe_tokenizer("mistral:tokenizer")
    assert tok_module._is_safe_tokenizer("tiktoken")


def test_empty_env_uses_defaults(monkeypatch):
    """Empty env var → empty frozenset → only 'default' passes."""
    import arachna.tokenizer as tok_module

    monkeypatch.setenv("ARACHNA_SAFE_TOKENIZERS", "")
    tok_module._SAFE_TOKENIZERS = frozenset()

    assert not tok_module._is_safe_tokenizer("tiktoken")
    assert tok_module._is_safe_tokenizer("default")
