"""Tests for collect_api.py (v2.0.0)."""

import json

import pytest

from arachna.api_errors import ProfileNotFoundError
from arachna.collect_api import collect


def test_collect_api_with_profile_dict(tmp_path, monkeypatch):
    """collect() with profile dict returns CollectResult."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = {
        "name_template": "chat-api",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    result = collect(profile=profile, output_dir="out")
    assert len(result.files) == 1
    assert len(result.parts) == 1
    assert result.tokens > 0
    assert "main.py" in result.parts[0]


def test_collect_api_with_profile_name(tmp_path, monkeypatch):
    """collect() with profile name looks up .arachna.json."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
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

    result = collect(profile="code")
    assert len(result.files) == 1


def test_collect_api_profile_not_found(tmp_path, monkeypatch):
    """collect() with unknown profile name raises ProfileNotFoundError."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"x": {"command": "echo hi", "max_tokens": 100}}})
    )

    with pytest.raises(ProfileNotFoundError):
        collect(profile="nonexistent")


def test_collect_api_with_query(tmp_path, monkeypatch):
    """collect() with query filters files."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass")
    (src / "utils.py").write_text("def helper(): pass")

    profile = {
        "name_template": "chat-q",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    result = collect(profile=profile, output_dir="out", query="auth")
    assert len(result.files) == 1
    assert "auth.py" in result.parts[0]


def test_collect_api_with_mode_repo_map(tmp_path, monkeypatch):
    """collect() with mode='repo-map' returns signatures only."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")

    profile = {
        "name_template": "chat-rm",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    result = collect(profile=profile, output_dir="out", mode="repo-map")
    assert len(result.files) == 1
    assert "def foo():" in result.parts[0]
    assert "return 1" not in result.parts[0]


def test_collect_api_merge_mode(tmp_path, monkeypatch):
    """collect() with merge=True appends files."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x = 1")

    profile = {
        "name_template": "chat-m",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    r1 = collect(profile=profile, output_dir="out", merge=True)
    r2 = collect(profile=profile, output_dir="out", merge=True)
    assert len(r1.files) == 1
    assert len(r2.files) == 1


def test_collect_api_incremental(tmp_path, monkeypatch):
    """collect() with incremental=True skips unchanged files."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x = 1")

    profile = {
        "name_template": "chat-inc",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    r1 = collect(profile=profile, output_dir="out", incremental=True)
    r2 = collect(profile=profile, output_dir="out", incremental=True)
    assert len(r1.files) == 1
    assert len(r2.files) == 0
