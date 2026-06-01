"""Error handling tests for gitignore.py."""

from pathlib import Path

from arachna.gitignore import load_gitignore_patterns


def test_gitignore_os_error_on_stat(tmp_path, monkeypatch):
    """Gitignore that raises OSError on stat is skipped gracefully.

    Monkeypatch is narrowed to only raise on .gitignore files by wrapping
    load_gitignore_patterns dependencies instead of Path.stat directly.
    """
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc")

    # Make the .gitignore file unreadable by removing read permission
    # then patch st_size to force the stat call to raise
    original_stat = Path.stat

    def mock_stat(self, *args, **kwargs):
        if self.name == ".gitignore" and self.parent == tmp_path:
            raise OSError("Permission denied")
        return original_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", mock_stat)
    patterns = load_gitignore_patterns(tmp_path)
    assert isinstance(patterns, list)


def test_gitignore_unicode_decode_error(tmp_path):
    """Gitignore with invalid UTF-8 is skipped gracefully."""
    (tmp_path / ".gitignore").write_bytes(b"\xff\xfe\x00\x01\x02\x03")
    patterns = load_gitignore_patterns(tmp_path)
    assert isinstance(patterns, list)


def test_gitignore_value_error_from_relative_to(tmp_path, monkeypatch):
    """Gitignore in subdirectory that raises ValueError on relative_to is skipped."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / ".gitignore").write_text("*.log")

    def failing_relative_to(self, other):
        raise ValueError("Path is outside root")

    monkeypatch.setattr(Path, "relative_to", failing_relative_to)
    patterns = load_gitignore_patterns(tmp_path)
    assert isinstance(patterns, list)
