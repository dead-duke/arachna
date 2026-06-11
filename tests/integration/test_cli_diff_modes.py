"""Integration tests for diff --mode structural/repo-map (v3.0)."""

import json

from tests.integration.conftest import _arachna


def test_diff_mode_structural(tmp_path, monkeypatch):
    """TC-117: diff --mode structural produces block-level diff."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
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

    _arachna("snapshot", "create", "--profile", "code", "--name", "struct-snap")
    (src / "main.py").write_text("def foo():\n    return 2\n")

    result = _arachna("diff", "--from", "struct-snap", "--profile", "code", "--mode", "structural")
    assert result.returncode == 0

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "MODIFIED" in content or "modified" in content


def test_diff_mode_repo_map(tmp_path, monkeypatch):
    """TC-118: diff --mode repo-map extracts signatures only."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n\ndef bar():\n    return 2\n")
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

    _arachna("snapshot", "create", "--profile", "code", "--name", "rm-snap")
    (src / "main.py").write_text("def foo():\n    return 3\n\ndef bar():\n    return 4\n")

    result = _arachna("diff", "--from", "rm-snap", "--profile", "code", "--mode", "repo-map")
    assert result.returncode == 0

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content


def test_diff_mode_structural_no_changes(tmp_path, monkeypatch):
    """TC-119: diff --mode structural with no changes exits cleanly."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
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

    _arachna("snapshot", "create", "--profile", "code", "--name", "nochg-snap")

    result = _arachna("diff", "--from", "nochg-snap", "--profile", "code", "--mode", "structural")
    assert result.returncode == 0
