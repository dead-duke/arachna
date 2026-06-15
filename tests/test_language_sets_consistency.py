"""TC-179: C_LIKE_LANGS and SCRIPT_LANGS consistency across modules."""

from arachna.domain.formatter import C_LIKE_LANGS as FMT_C_LIKE
from arachna.domain.formatter import SCRIPT_LANGS as FMT_SCRIPT
from arachna.domain.splitter import C_LIKE_LANGS as SP_C_LIKE
from arachna.domain.splitter import SCRIPT_LANGS as SP_SCRIPT
from arachna.watch.differ_structural import C_LIKE_LANGS as DS_C_LIKE
from arachna.watch.differ_structural import SCRIPT_LANGS as DS_SCRIPT


def test_c_like_langs_identical():
    """All modules that import from formatter have identical C_LIKE_LANGS."""
    assert FMT_C_LIKE == DS_C_LIKE, (
        f"formatter: {sorted(FMT_C_LIKE - DS_C_LIKE)} extra, "
        f"differ_structural: {sorted(DS_C_LIKE - FMT_C_LIKE)} extra"
    )
    assert FMT_C_LIKE == SP_C_LIKE, (
        f"formatter: {sorted(FMT_C_LIKE - SP_C_LIKE)} extra, "
        f"splitter: {sorted(SP_C_LIKE - FMT_C_LIKE)} extra"
    )


def test_script_langs_identical():
    """All modules that import from formatter have identical SCRIPT_LANGS."""
    assert FMT_SCRIPT == DS_SCRIPT, (
        f"formatter: {sorted(FMT_SCRIPT - DS_SCRIPT)} extra, "
        f"differ_structural: {sorted(DS_SCRIPT - FMT_SCRIPT)} extra"
    )
    assert FMT_SCRIPT == SP_SCRIPT, (
        f"formatter: {sorted(FMT_SCRIPT - SP_SCRIPT)} extra, "
        f"splitter: {sorted(SP_SCRIPT - FMT_SCRIPT)} extra"
    )


def test_zig_and_gleam_in_c_like():
    """zig and gleam are in C_LIKE_LANGS (fixed from v2.7.0 divergence)."""
    assert "zig" in FMT_C_LIKE
    assert "gleam" in FMT_C_LIKE
