"""Tests for _parse_output_dir with --output-dir and -o flags."""

from arachna.cli._helpers import parse_output_dir
from arachna.config.profile_config import ArachnaConfig


def _make_args(output_dir=None):
    from argparse import Namespace

    return Namespace(output_dir=output_dir)


def test_parse_output_dir_flag():
    result = parse_output_dir(
        _make_args(output_dir="/custom/path"), ArachnaConfig(output_dir="default")
    )
    assert result == "/custom/path"


def test_parse_output_dir_fallback():
    result = parse_output_dir(_make_args(), ArachnaConfig(output_dir="config_default"))
    assert result == "config_default"


def test_parse_output_dir_no_config_key():
    result = parse_output_dir(_make_args(), ArachnaConfig())
    assert result == "arachna_context"
