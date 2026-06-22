"""Integration tests for diff line numbers."""

import json

from tests.integration.conftest import _arachna


def test_diff_line_numbers_flag(tmp_path):
    """diff --line-numbers shows line numbers in REMOVED/ADDED blocks."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("line1\nline2\nline3\n")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )
    _arachna("snapshot", "create", "--profile", "code", "--name", "ln-snap", cwd=tmp_path)
    (src / "main.py").write_text("line1\nchanged\nline3\n")
    result = _arachna(
        "diff", "--from", "ln-snap", "--profile", "code", "--line-numbers", cwd=tmp_path
    )
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "2|" in content


def test_diff_line_numbers_no_flag_no_numbers(tmp_path):
    """diff without --line-numbers does not show line numbers."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("line1\nline2\nline3\n")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )
    _arachna("snapshot", "create", "--profile", "code", "--name", "noln-snap", cwd=tmp_path)
    (src / "main.py").write_text("line1\nchanged\nline3\n")
    result = _arachna("diff", "--from", "noln-snap", "--profile", "code", cwd=tmp_path)
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "REMOVED" in content or "ADDED" in content


def test_diff_added_file_line_numbers(tmp_path):
    """diff --line-numbers on added file shows line numbers."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "old.py").write_text("original\n")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )
    _arachna("snapshot", "create", "--profile", "code", "--name", "addln-snap", cwd=tmp_path)
    (src / "new.py").write_text("line1\nline2\nline3\n")
    result = _arachna(
        "diff", "--from", "addln-snap", "--profile", "code", "--line-numbers", cwd=tmp_path
    )
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "1| line1" in content
