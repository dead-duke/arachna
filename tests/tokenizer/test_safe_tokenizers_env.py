"""Tests for ARACHNA_SAFE_TOKENIZERS env var."""

import os

import pytest


@pytest.fixture(autouse=True)
def _restore_safe_tokenizers():
    import arachna.tokenizer as tok_module

    original = tok_module._SAFE_TOKENIZERS
    yield
    tok_module._SAFE_TOKENIZERS = original


def test_custom_safe_tokenizer_via_env(monkeypatch):
    import arachna.tokenizer as tok_module

    monkeypatch.setenv("ARACHNA_SAFE_TOKENIZERS", "tiktoken,transformers,mistral")
    tok_module._SAFE_TOKENIZERS = frozenset(
        os.environ.get("ARACHNA_SAFE_TOKENIZERS", "tiktoken,transformers").split(",")
    )
    assert tok_module._is_safe_tokenizer("mistral:tokenizer")
    assert tok_module._is_safe_tokenizer("tiktoken")
    assert tok_module._is_safe_tokenizer("transformers")


def test_unknown_tokenizer_still_blocked(monkeypatch):
    import arachna.tokenizer as tok_module

    monkeypatch.setenv("ARACHNA_SAFE_TOKENIZERS", "tiktoken")
    tok_module._SAFE_TOKENIZERS = frozenset(
        os.environ.get("ARACHNA_SAFE_TOKENIZERS", "tiktoken,transformers").split(",")
    )
    assert not tok_module._is_safe_tokenizer("mistral:tokenizer")
    assert tok_module._is_safe_tokenizer("tiktoken")


def test_default_still_safe(monkeypatch):
    import arachna.tokenizer as tok_module

    monkeypatch.setenv("ARACHNA_SAFE_TOKENIZERS", "")
    tok_module._SAFE_TOKENIZERS = frozenset()
    assert tok_module._is_safe_tokenizer("default")
