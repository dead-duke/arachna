from arachna.collector import collect


def test_collect_incremental_skips_unchanged(tmp_path, monkeypatch):
    """Integration test: collect with incremental=True skips unchanged files."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("unchanged")
    out = tmp_path / "out"
    out.mkdir()

    profile = {
        "name_template": "chat-test",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    # First run — should collect the file
    created1, _ = collect(profile, "P", "out", incremental=True)
    assert len(created1) == 1

    # Second run — file unchanged, should produce no output
    created2, _ = collect(profile, "P", "out", incremental=True)
    assert len(created2) == 0


def test_collect_incremental_detects_modified(tmp_path, monkeypatch):
    """Integration test: collect with incremental=True detects modified files."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    fp = src / "a.py"
    fp.write_text("original")
    out = tmp_path / "out"
    out.mkdir()

    profile = {
        "name_template": "chat-test",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    # First run
    created1, _ = collect(profile, "P", "out", incremental=True)
    assert len(created1) == 1

    # Modify the file
    fp.write_text("modified")

    # Second run — should detect modification and collect again
    created2, _ = collect(profile, "P", "out", incremental=True)
    assert len(created2) == 1


def test_collect_incremental_detects_new_file(tmp_path, monkeypatch):
    """Integration test: collect with incremental=True detects newly added files."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("existing")
    out = tmp_path / "out"
    out.mkdir()

    profile = {
        "name_template": "chat-test",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    # First run — collect a.py
    created1, _ = collect(profile, "P", "out", incremental=True)
    assert len(created1) == 1

    # Add new file
    (src / "b.py").write_text("new file")

    # Second run — should detect new file
    created2, _ = collect(profile, "P", "out", incremental=True)
    assert len(created2) == 1
