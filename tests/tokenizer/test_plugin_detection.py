"""Tests for tokenizer plugin detection — tiktoken/transformers lazy import."""

from unittest.mock import patch

import pytest

from arachna.tokenizer import (
    _check_tokenizer_plugins,
    _has_tiktoken,
    _has_transformers,
    load_tokenizer,
)


def test_has_tiktoken_not_installed():
    with patch("arachna.tokenizer._HAS_TIKTOKEN", False):
        assert not _has_tiktoken()


def test_has_tiktoken_installed():
    with patch("arachna.tokenizer._HAS_TIKTOKEN", True):
        assert _has_tiktoken()


def test_has_transformers_not_installed():
    with patch("arachna.tokenizer._HAS_TRANSFORMERS", False):
        assert not _has_transformers()


def test_has_transformers_installed():
    with patch("arachna.tokenizer._HAS_TRANSFORMERS", True):
        assert _has_transformers()


def test_check_tokenizer_plugins_none_installed():
    with patch.dict("sys.modules", {"tiktoken": None, "transformers": None}):
        _check_tokenizer_plugins()
        assert not _has_tiktoken()
        assert not _has_transformers()


def test_check_tokenizer_plugins_tiktoken_installed():
    class FakeTiktoken:
        pass

    with patch.dict("sys.modules", {"tiktoken": FakeTiktoken}):
        _check_tokenizer_plugins()
        assert _has_tiktoken()


def test_load_tokenizer_tiktoken_not_installed():
    with (
        patch("arachna.tokenizer._has_tiktoken", return_value=False),
        pytest.raises(ValueError, match="tiktoken is not installed"),
    ):
        load_tokenizer("tiktoken:cl100k_base")


def test_load_tokenizer_transformers_not_installed():
    with (
        patch("arachna.tokenizer._has_transformers", return_value=False),
        pytest.raises(ValueError, match="transformers is not installed"),
    ):
        load_tokenizer("transformers:gpt2")


def test_load_tokenizer_tiktoken_installed():
    with (
        patch("arachna.tokenizer._has_tiktoken", return_value=True),
        patch("arachna.tokenizer._load_tiktoken", return_value=lambda t: 42),
    ):
        tok = load_tokenizer("tiktoken")
        assert tok("anything") == 42


def test_load_tokenizer_transformers_installed():
    with (
        patch("arachna.tokenizer._has_transformers", return_value=True),
        patch("arachna.tokenizer._load_transformers", return_value=lambda t: 99),
    ):
        tok = load_tokenizer("transformers:gpt2")
        assert tok("anything") == 99
