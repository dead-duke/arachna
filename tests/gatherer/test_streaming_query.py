"""Tests for streaming mode with query filtering (v2.9.2)."""

from arachna.collector import collect


def test_streaming_full_mode_with_query(tmp_path, monkeypatch):
    """Streaming full mode filters files by query before reading content."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass")
    (src / "utils.py").write_text("def helper(): pass")

    out = tmp_path / "out"
    out.mkdir()

    profile = {
        "name_template": "chat-q",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    created, _, parts = collect(profile, "Test", "out", mode="full", query="auth")
    assert len(created) >= 1
    all_content = "".join(parts)
    assert "auth.py" in all_content
    assert "utils.py" not in all_content


def test_streaming_full_mode_without_query_collects_all(tmp_path, monkeypatch):
    """Streaming full mode without query collects all files."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass")
    (src / "utils.py").write_text("def helper(): pass")

    out = tmp_path / "out"
    out.mkdir()

    profile = {
        "name_template": "chat-all",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    created, _, parts = collect(profile, "Test", "out", mode="full")
    assert len(created) >= 1
    all_content = "".join(parts)
    assert "auth.py" in all_content
    assert "utils.py" in all_content
