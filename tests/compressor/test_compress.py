from arachna.compressor import compress, estimate_savings


def test_collapse_blank_lines():
    text = "a\n\n\n\nb"
    result = compress(text)
    assert result == "a\n\nb"


def test_strip_trailing_whitespace():
    text = "hello   \nworld\t\t\n"
    result = compress(text)
    assert result == "hello\nworld\n"


def test_empty_text():
    assert compress("") == ""


def test_no_change():
    text = "hello\n\nworld"
    assert compress(text) == text


def test_preserves_indentation():
    text = "    indented\n        deeper"
    result = compress(text)
    assert "    indented" in result
    assert "        deeper" in result


def test_estimate_savings():
    orig = "a\n\n\n\n\n\nb" * 100
    comp = compress(orig)
    o, c, pct = estimate_savings(orig, comp)
    assert c < o
    assert pct > 0
