"""Tests for TOCTOU protection in SafePath I/O methods."""

import tempfile
from pathlib import Path

import pytest

from arachna.domain.path_utils import SafePath


@pytest.fixture
def outside_dir():
    """Create a directory outside tmp_path that SafePath cannot access."""
    d = tempfile.mkdtemp()
    yield Path(d)
    import shutil

    shutil.rmtree(d, ignore_errors=True)


def test_read_text_detects_symlink_swap_outside_root(tmp_path, outside_dir):
    """SafePath.read_text raises ValueError if symlink was swapped to point outside root."""
    (outside_dir / "secret.txt").write_text("secret")

    safe = SafePath(tmp_path / "link.txt", tmp_path)
    safe._path.symlink_to(tmp_path / "real.txt")
    (tmp_path / "real.txt").write_text("safe content")

    # Swap symlink to point outside root
    safe._path.unlink()
    safe._path.symlink_to(outside_dir / "secret.txt")

    with pytest.raises(ValueError, match="Path traversal detected at I/O time"):
        safe.read_text()


def test_write_text_detects_symlink_swap_outside_root(tmp_path, outside_dir):
    """SafePath.write_text raises ValueError if symlink was swapped to point outside root."""
    safe = SafePath(tmp_path / "link.txt", tmp_path)
    safe._path.symlink_to(tmp_path / "real.txt")
    (tmp_path / "real.txt").write_text("original")

    safe._path.unlink()
    safe._path.symlink_to(outside_dir / "secret.txt")

    with pytest.raises(ValueError, match="Path traversal detected at I/O time"):
        safe.write_text("malicious content")


def test_read_bytes_detects_symlink_swap_outside_root(tmp_path, outside_dir):
    """SafePath.read_bytes raises ValueError if symlink was swapped to point outside root."""
    (outside_dir / "data.bin").write_bytes(b"\x00")

    safe = SafePath(tmp_path / "link.bin", tmp_path)
    safe._path.symlink_to(tmp_path / "real.bin")
    (tmp_path / "real.bin").write_bytes(b"ok")

    safe._path.unlink()
    safe._path.symlink_to(outside_dir / "data.bin")

    with pytest.raises(ValueError, match="Path traversal detected at I/O time"):
        safe.read_bytes()


def test_write_bytes_detects_symlink_swap_outside_root(tmp_path, outside_dir):
    """SafePath.write_bytes raises ValueError if symlink was swapped to point outside root."""
    safe = SafePath(tmp_path / "link.bin", tmp_path)
    safe._path.symlink_to(tmp_path / "real.bin")
    (tmp_path / "real.bin").write_bytes(b"original")

    safe._path.unlink()
    safe._path.symlink_to(outside_dir / "evil.bin")

    with pytest.raises(ValueError, match="Path traversal detected at I/O time"):
        safe.write_bytes(b"malicious")


def test_read_text_allows_normal_file_inside_root(tmp_path):
    """SafePath.read_text works normally when no symlink swap happened."""
    safe = SafePath(tmp_path / "normal.txt", tmp_path)
    safe.write_text("hello")
    assert safe.read_text() == "hello"


def test_symlink_swap_to_parent_dir_is_caught(tmp_path):
    """TOCTOU check catches symlink to parent of root."""
    inside_dir = tmp_path / "inside"
    inside_dir.mkdir()

    safe = SafePath(inside_dir / "link.txt", tmp_path)
    safe._path.symlink_to(inside_dir / "real.txt")
    (inside_dir / "real.txt").write_text("ok")

    safe._path.unlink()
    safe._path.symlink_to(tmp_path.parent / "outside.txt")

    with pytest.raises(ValueError, match="Path traversal detected at I/O time"):
        safe.read_text()
