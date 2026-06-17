"""Tests for path_utils.py — v4.2.0."""

from pathlib import Path

from arachna.domain.path_utils import validate_path


def test_validate_path_within_root(tmp_path):
    assert validate_path(tmp_path / "file.py", tmp_path)


def test_validate_path_nested_within_root(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    assert validate_path(sub / "file.py", tmp_path)


def test_validate_path_outside_root(tmp_path):
    assert not validate_path(Path("/etc/passwd"), tmp_path)


def test_validate_path_symlink_not_resolved_to_outside(tmp_path):
    link = tmp_path / "link"
    real = tmp_path / "real"
    real.mkdir()
    link.symlink_to(real)
    assert validate_path(link, tmp_path)


def test_validate_path_equal(tmp_path):
    assert validate_path(tmp_path, tmp_path)


def test_validate_path_nonexistent_inside(tmp_path):
    assert validate_path(tmp_path / "nonexistent" / "file.py", tmp_path)


def test_validate_path_parent_root(tmp_path):
    assert not validate_path(tmp_path.parent, tmp_path)


def test_validate_path_root_os_error(tmp_path):
    """When root.resolve() raises OSError, validate_path returns False."""
    assert not validate_path(tmp_path / "file.py", tmp_path / "nonexistent_root")
