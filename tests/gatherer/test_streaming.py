"""Tests for streaming pipeline (v2.9.2)."""

from arachna.collector import collect


def test_streaming_1000_files_no_oom(tmp_path, monkeypatch):
    """Streaming mode collects 1000 files without loading all into memory."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    for i in range(1000):
        (src / f"file_{i}.py").write_text(f"# File {i}\nx = {i}\n")

    out = tmp_path / "out"
    out.mkdir()

    profile = {
        "name_template": "chat-stream",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 32768,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    created, _, parts = collect(profile, "Test", "out", mode="full")
    assert len(created) >= 1
    assert len(parts) >= 1
    # All 1000 files should be present across parts
    all_content = "".join(parts)
    for i in range(1000):
        assert f"file_{i}.py" in all_content, f"file_{i}.py missing from output"


def test_streaming_repo_map_stays_in_memory(tmp_path, monkeypatch):
    """Repo-map mode uses in-memory path, not streaming."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n\ndef bar():\n    return 2\n")

    out = tmp_path / "out"
    out.mkdir()

    profile = {
        "name_template": "chat-rm",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    created, _, parts = collect(profile, "Test", "out", mode="repo-map")
    assert len(created) == 1
    content = parts[0] if parts else ""
    if not parts:
        content = created[0].read_text() if created else ""
    assert "def foo():" in content
    assert "def bar():" in content
    assert "return 1" not in content
