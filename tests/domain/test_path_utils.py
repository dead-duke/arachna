"""Tests for path_utils.py — v4.2.0 + SafePath v5.1.0."""

from pathlib import Path

import pytest

from arachna.domain.path_utils import SafePath, validate_path

# -- validate_path -------------------------------------------------


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


# -- SafePath -------------------------------------------------------


def test_safepath_create_within_root(tmp_path):
    root = SafePath(tmp_path)
    f = root / "file.py"
    assert str(f) == str(tmp_path / "file.py")


def test_safepath_rejects_path_outside_root(tmp_path):
    with pytest.raises(ValueError, match="Path traversal"):
        SafePath("/etc/passwd", tmp_path)


def test_safepath_nested_within_root(tmp_path):
    root = SafePath(tmp_path)
    sub = root / "sub"
    sub.mkdir(parents=True)
    f = sub / "file.py"
    f.write_text("hello")
    assert f.read_text() == "hello"


def test_safepath_rejects_dot_dot_traversal(tmp_path):
    root = SafePath(tmp_path)
    with pytest.raises(ValueError, match="Path traversal"):
        _ = root / "../../etc/passwd"


def test_safepath_properties(tmp_path):
    root = SafePath(tmp_path)
    f = root / "test.txt"
    f.write_text("content")
    assert f.name == "test.txt"
    assert f.suffix == ".txt"
    assert f.stem == "test"
    assert f.exists()
    assert f.is_file()
    assert not f.is_dir()


def test_safepath_mkdir_and_isdir(tmp_path):
    root = SafePath(tmp_path)
    sub = root / "mydir"
    sub.mkdir()
    assert sub.is_dir()
    assert not sub.is_file()


def test_safepath_unlink(tmp_path):
    root = SafePath(tmp_path)
    f = root / "to_delete.txt"
    f.write_text("delete me")
    assert f.exists()
    f.unlink()
    assert not f.exists()


def test_safepath_glob(tmp_path):
    root = SafePath(tmp_path)
    (root / "a.py").write_text("a")
    (root / "b.py").write_text("b")
    (root / "c.txt").write_text("c")
    py_files = list(root.glob("*.py"))
    assert len(py_files) == 2
    names = {f.name for f in py_files}
    assert names == {"a.py", "b.py"}


def test_safepath_rglob(tmp_path):
    root = SafePath(tmp_path)
    sub = root / "sub"
    sub.mkdir()
    (sub / "nested.py").write_text("nested")
    matches = list(root.rglob("*.py"))
    assert len(matches) == 1
    assert matches[0].name == "nested.py"


def test_safepath_str_and_repr(tmp_path):
    root = SafePath(tmp_path)
    f = root / "test.py"
    assert str(f) == str(tmp_path / "test.py")
    assert "SafePath" in repr(f)


def test_safepath_resolve(tmp_path):
    root = SafePath(tmp_path)
    f = root / "test.py"
    resolved = f.resolve()
    assert str(resolved) == str(Path(tmp_path / "test.py").resolve())


def test_safepath_parent(tmp_path):
    root = SafePath(tmp_path)
    f = root / "sub" / "file.py"
    assert str(f.parent) == str(tmp_path / "sub")
