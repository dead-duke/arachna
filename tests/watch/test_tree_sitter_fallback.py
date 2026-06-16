"""Tests for tree-sitter lazy import and fallback in differ_structural.py."""

from unittest.mock import patch

from arachna.watch.differ_structural import (
    _check_plugins,
    _has_tree_sitter_for,
    structural_diff_for_lang,
)


def test_has_tree_sitter_for_none_installed():
    """_has_tree_sitter_for returns False when nothing installed."""
    with (
        patch("arachna.watch.differ_structural._HAS_TS_JS", False),
        patch("arachna.watch.differ_structural._HAS_TS_TS", False),
        patch("arachna.watch.differ_structural._HAS_TS_GO", False),
    ):
        assert not _has_tree_sitter_for("javascript")
        assert not _has_tree_sitter_for("typescript")
        assert not _has_tree_sitter_for("go")
        assert not _has_tree_sitter_for("python")


def test_has_tree_sitter_for_js_installed():
    with (
        patch("arachna.watch.differ_structural._HAS_TS_JS", True),
        patch("arachna.watch.differ_structural._HAS_TS_TS", False),
        patch("arachna.watch.differ_structural._HAS_TS_GO", False),
    ):
        assert _has_tree_sitter_for("javascript")
        assert not _has_tree_sitter_for("typescript")


def test_has_tree_sitter_for_ts_installed():
    with (
        patch("arachna.watch.differ_structural._HAS_TS_JS", False),
        patch("arachna.watch.differ_structural._HAS_TS_TS", True),
        patch("arachna.watch.differ_structural._HAS_TS_GO", False),
    ):
        assert _has_tree_sitter_for("typescript")
        assert _has_tree_sitter_for("tsx")


def test_check_plugins_no_tree_sitter():
    with patch.dict("sys.modules", {"tree_sitter": None}):
        _check_plugins()
        assert not _has_tree_sitter_for("javascript")


def test_structural_diff_js_fallback_warning():
    """JS structural diff without tree-sitter falls back with warning."""
    old = "function foo() {\n    return 1;\n}\n"
    new = "function foo() {\n    return 2;\n}\n"

    with (
        patch("arachna.watch.differ_structural._has_tree_sitter_for", return_value=False),
    ):
        result = structural_diff_for_lang(old, new, "src/app.js", "javascript")
        assert isinstance(result, str)
        assert len(result) > 0
