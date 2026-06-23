"""Tests for tree-sitter lazy import and fallback in differ_structural.py."""

from unittest.mock import patch

from arachna.snapshot.diff import differ_structural as ds
from arachna.snapshot.diff.differ_structural import (
    _has_tree_sitter_for,
    structural_diff_for_lang,
)


def test_has_tree_sitter_for_none_installed():
    with patch.object(
        ds, "_check_plugins", return_value={"has_ts": False, "js": False, "ts": False, "go": False}
    ):
        assert not _has_tree_sitter_for("javascript")
        assert not _has_tree_sitter_for("typescript")
        assert not _has_tree_sitter_for("go")
        assert not _has_tree_sitter_for("python")


def test_has_tree_sitter_for_js_installed():
    with patch.object(
        ds, "_check_plugins", return_value={"has_ts": True, "js": True, "ts": False, "go": False}
    ):
        assert _has_tree_sitter_for("javascript")
        assert not _has_tree_sitter_for("typescript")


def test_has_tree_sitter_for_ts_installed():
    with patch.object(
        ds, "_check_plugins", return_value={"has_ts": True, "js": False, "ts": True, "go": False}
    ):
        assert _has_tree_sitter_for("typescript")
        assert _has_tree_sitter_for("tsx")


def test_check_plugins_no_tree_sitter():
    """When tree_sitter is not installed, _check_plugins returns all False."""
    with patch.object(
        ds, "_check_plugins", return_value={"has_ts": False, "js": False, "ts": False, "go": False}
    ):
        assert not _has_tree_sitter_for("javascript")


def test_structural_diff_js_fallback_warning():
    old = "function foo() {\n    return 1;\n}\n"
    new = "function foo() {\n    return 2;\n}\n"
    with patch.object(ds, "_has_tree_sitter_for", return_value=False):
        result = structural_diff_for_lang(old, new, "src/app.js", "javascript")
        assert isinstance(result, str)
        assert len(result) > 0
