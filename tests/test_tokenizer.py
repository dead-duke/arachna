"""Tests for tokenizer — conservative token estimation."""

from arachna.tokenizer import count_tokens


def test_empty_string():
    assert count_tokens("") == 1


def test_single_char():
    assert count_tokens("a") == 1
    assert count_tokens("ф") == 1


def test_four_chars_one_token():
    assert count_tokens("abcd") == 1
    assert count_tokens("абвг") == 1


def test_eight_chars_two_tokens():
    assert count_tokens("abcdefgh") == 2


def test_emoji_single():
    assert count_tokens("🚀") == 1


def test_emoji_multiple():
    assert count_tokens("🚀🚀🚀🚀") == 1


def test_cjk_chars():
    # "日本語テスト" is 6 characters, 6 // 4 = 1 token
    assert count_tokens("日本語テスト") == 1


def test_long_text():
    assert count_tokens("a" * 1000) == 250


def test_newlines_and_whitespace():
    assert count_tokens("a\nb\nc\nd") == 1
