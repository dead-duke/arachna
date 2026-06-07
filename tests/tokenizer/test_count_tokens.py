from arachna.tokenizer import count_tokens


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
    # 6 CJK characters, 6 // 4 = 1 token
    assert count_tokens("日本語テスト") == 1


def test_cjk_longer():
    # 12 CJK characters, 12 // 4 = 3 tokens
    assert count_tokens("日本語テスト文章生成生成") == 3


def test_long_text():
    assert count_tokens("a" * 1000) == 250


def test_newlines():
    assert count_tokens("a\nb\nc\nd") == 1
