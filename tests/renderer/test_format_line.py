from arachna.cli.renderer import _format_line


def test_basic():
    r = _format_line(500, 16000, "main.py")
    assert "500 tokens" in r
    assert "3.1%" in r
    assert "main.py" in r


def test_zero_tokens():
    assert "<0.1%" in _format_line(0, 16000, "x")


def test_full():
    assert "100.0%" in _format_line(16000, 16000, "x")


def test_tiny():
    assert "<0.1%" in _format_line(1, 32000, "x")


def test_zero_max():
    assert "0.0%" in _format_line(100, 0, "x")


def test_long_name():
    name = "a" * 80
    assert name in _format_line(100, 1000, name)
