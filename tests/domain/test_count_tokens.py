from hypothesis import given
from hypothesis import strategies as st

from arachna.domain.tokenizer import count_tokens


def test_empty_string():
    assert count_tokens("") == 1


def test_single_char():
    assert count_tokens("a") == 1


def test_cyrillic():
    assert count_tokens("ф") == 1


def test_four_chars():
    assert count_tokens("abcd") == 1


def test_eight_chars():
    assert count_tokens("abcdefgh") == 2


def test_emoji():
    assert count_tokens("🚀") == 1


def test_cjk():
    assert count_tokens("日本語テスト") == 1


def test_cjk_longer():
    assert count_tokens("日本語テスト文章生成生成") == 3


def test_long_text():
    assert count_tokens("a" * 1000) == 250


def test_newlines():
    assert count_tokens("a\nb\nc\nd") == 1


def test_emoji_sequence():
    family = "👨‍👩‍👧‍👦"
    assert count_tokens(family) == 1


def test_combining_characters():
    text = "cafe\u0301"
    assert count_tokens(text) == 1


def test_rtl_text():
    text = "مرحبا بالعالم"
    assert count_tokens(text) == 3


def test_mixed_unicode():
    text = "Hello世界🚀"
    assert count_tokens(text) == 2


def test_zero_width_joiners():
    text = "\u200d\u200d\u200d\u200d"
    assert count_tokens(text) == 1


@given(st.text())
def test_count_tokens_always_positive(text):
    assert count_tokens(text) >= 1


@given(st.text())
def test_count_tokens_reasonable_upper_bound(text):
    assert count_tokens(text) <= len(text) + 1


@given(st.text(min_size=4))
def test_count_tokens_monotonic_approx(text):
    assert count_tokens(text) >= count_tokens(text[: len(text) // 2])


@given(st.text(), st.text())
def test_count_tokens_concatenation_upper_bound(a, b):
    assert count_tokens(a + b) <= count_tokens(a) + count_tokens(b) + 1
