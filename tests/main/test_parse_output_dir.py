"""TC-181: _parse_output_dir parses --output-dir and -o flags."""

from arachna.cli_watch import _parse_output_dir


def test_parse_output_dir_long_flag():
    """--output-dir extracts value."""
    argv = ["arachna", "--diff", "--output-dir", "/custom/path"]
    result = _parse_output_dir(argv, {"output_dir": "default"})
    assert result == "/custom/path"


def test_parse_output_dir_short_flag():
    """-o extracts value."""
    argv = ["arachna", "--diff", "-o", "/short/path"]
    result = _parse_output_dir(argv, {"output_dir": "default"})
    assert result == "/short/path"


def test_parse_output_dir_fallback():
    """No flag — uses config default."""
    argv = ["arachna", "--diff"]
    result = _parse_output_dir(argv, {"output_dir": "config_default"})
    assert result == "config_default"


def test_parse_output_dir_no_config_key():
    """No output_dir in config — returns '.'."""
    argv = ["arachna", "--diff"]
    result = _parse_output_dir(argv, {})
    assert result == "."


def test_parse_output_dir_long_without_value():
    """--output-dir at end without value — returns config default."""
    argv = ["arachna", "--diff", "--output-dir"]
    result = _parse_output_dir(argv, {"output_dir": "fallback"})
    assert result == "fallback"


def test_parse_output_dir_short_without_value():
    """-o at end without value — returns config default."""
    argv = ["arachna", "--diff", "-o"]
    result = _parse_output_dir(argv, {"output_dir": "fallback"})
    assert result == "fallback"
