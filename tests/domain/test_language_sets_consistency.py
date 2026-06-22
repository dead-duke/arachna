"""Tests for C_LIKE_LANGS and SCRIPT_LANGS consistency across dispatch mappings.

After v4.0.1 refactoring, language sets are defined in formatter.py only.
This test verifies that language_dispatch.py mappings cover all languages
and that splitter imports match formatter (same source).
"""

from arachna.domain.execution.splitter import C_LIKE_LANGS as SP_C_LIKE
from arachna.domain.execution.splitter import SCRIPT_LANGS as SP_SCRIPT
from arachna.domain.formatting.formatter import C_LIKE_LANGS, SCRIPT_LANGS
from arachna.domain.tokenization.language_dispatch import BLOCK_PARSERS, HEADER_PARSERS


def test_c_like_langs_identical_in_splitter():
    """Splitter imports C_LIKE_LANGS from formatter -- must be identical."""
    assert C_LIKE_LANGS == SP_C_LIKE, (
        f"formatter: {sorted(C_LIKE_LANGS - SP_C_LIKE)} extra, "
        f"splitter: {sorted(SP_C_LIKE - C_LIKE_LANGS)} extra"
    )


def test_script_langs_identical_in_splitter():
    """Splitter imports SCRIPT_LANGS from formatter -- must be identical."""
    assert SCRIPT_LANGS == SP_SCRIPT, (
        f"formatter: {sorted(SCRIPT_LANGS - SP_SCRIPT)} extra, "
        f"splitter: {sorted(SP_SCRIPT - SCRIPT_LANGS)} extra"
    )


def test_block_parsers_cover_all_c_like():
    """BLOCK_PARSERS has entries for every language in C_LIKE_LANGS."""
    for lang in C_LIKE_LANGS:
        assert lang in BLOCK_PARSERS, f"C_LIKE_LANGS member '{lang}' missing from BLOCK_PARSERS"
    assert "gdscript" in BLOCK_PARSERS


def test_block_parsers_cover_all_script():
    """BLOCK_PARSERS has entries for every language in SCRIPT_LANGS."""
    for lang in SCRIPT_LANGS:
        assert lang in BLOCK_PARSERS, f"SCRIPT_LANGS member '{lang}' missing from BLOCK_PARSERS"


def test_block_parsers_has_python():
    """BLOCK_PARSERS has python entry."""
    assert "python" in BLOCK_PARSERS


def test_header_parsers_cover_all_c_like():
    """HEADER_PARSERS has entries for every language in C_LIKE_LANGS."""
    for lang in C_LIKE_LANGS:
        assert lang in HEADER_PARSERS, f"C_LIKE_LANGS member '{lang}' missing from HEADER_PARSERS"
    assert "gdscript" in HEADER_PARSERS


def test_header_parsers_cover_all_script():
    """HEADER_PARSERS has entries for every language in SCRIPT_LANGS."""
    for lang in SCRIPT_LANGS:
        assert lang in HEADER_PARSERS, f"SCRIPT_LANGS member '{lang}' missing from HEADER_PARSERS"


def test_header_parsers_has_python():
    """HEADER_PARSERS has python entry."""
    assert "python" in HEADER_PARSERS
