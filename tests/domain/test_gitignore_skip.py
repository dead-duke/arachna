"""Tests for _should_skip_gitignore edge cases."""

from pathlib import Path

from arachna.domain.execution.gitignore import _should_skip_gitignore


def test_should_skip_not_a_file(tmp_path):
    """Returns True when path is not a file."""
    assert _should_skip_gitignore(tmp_path / "nonexistent", tmp_path)


def test_should_skip_symlink_parent(tmp_path):
    """Returns True when parent is symlink."""
    real = tmp_path / "real"
    real.mkdir()
    (real / ".gitignore").write_text("*.pyc")
    link = tmp_path / "link"
    link.symlink_to(real)
    assert _should_skip_gitignore(link / ".gitignore", tmp_path)


def test_should_skip_value_error_on_relative_to(tmp_path, monkeypatch):
    """Returns True when relative_to raises ValueError."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / ".gitignore").write_text("*.log")

    def failing_relative_to(self, other):
        raise ValueError("outside root")

    monkeypatch.setattr(Path, "relative_to", failing_relative_to)
    assert _should_skip_gitignore(sub / ".gitignore", tmp_path)
