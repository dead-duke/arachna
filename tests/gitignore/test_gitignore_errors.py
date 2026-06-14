"""Error handling tests for gitignore.py."""

from pathlib import Path

from arachna.gitignore import load_gitignore_patterns


def test_gitignore_os_error_on_st_size(tmp_path, monkeypatch):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc")

    original_st_size = Path.stat

    def mock_stat(self, *args, **kwargs):
        result = original_st_size(self, *args, **kwargs)
        if self.name == ".gitignore" and self.parent == tmp_path:

            class MockStatResult:
                st_mode = result.st_mode
                st_mtime = result.st_mtime

                @property
                def st_size(self):
                    raise OSError("Permission denied")

            return MockStatResult()
        return result

    monkeypatch.setattr(Path, "stat", mock_stat)
    patterns = load_gitignore_patterns(tmp_path)
    assert isinstance(patterns, list)


def test_gitignore_unicode_decode_error(tmp_path):
    (tmp_path / ".gitignore").write_bytes(b"\xff\xfe\x00\x01\x02\x03")
    patterns = load_gitignore_patterns(tmp_path)
    assert isinstance(patterns, list)


def test_gitignore_value_error_from_relative_to(tmp_path, monkeypatch):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / ".gitignore").write_text("*.log")

    def failing_relative_to(self, other):
        raise ValueError("Path is outside root")

    monkeypatch.setattr(Path, "relative_to", failing_relative_to)
    patterns = load_gitignore_patterns(tmp_path)
    assert isinstance(patterns, list)
