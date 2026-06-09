"""TC-181: _parse_output_dir parses --output-dir and -o flags — updated for v3.0."""

from arachna.__main__ import _parse_output_dir


def _make_args(output_dir=None):
    from argparse import Namespace

    return Namespace(output_dir=output_dir)


def test_parse_output_dir_flag():
    """--output-dir extracts value from args."""
    result = _parse_output_dir(_make_args(output_dir="/custom/path"), {"output_dir": "default"})
    assert result == "/custom/path"


def test_parse_output_dir_fallback():
    """No flag — uses config default."""
    result = _parse_output_dir(_make_args(), {"output_dir": "config_default"})
    assert result == "config_default"


def test_parse_output_dir_no_config_key():
    """No output_dir in config — returns '.'."""
    result = _parse_output_dir(_make_args(), {})
    assert result == "."
