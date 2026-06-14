from arachna.collector import collect


def test_collect_incremental_skips_unchanged(tmp_path):
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

    created1, _, _ = collect(profile, "P", "out", incremental=True, root=tmp_path)
    assert len(created1) == 1

    created2, _, _ = collect(profile, "P", "out", incremental=True, root=tmp_path)
    assert len(created2) == 0


def test_collect_incremental_detects_modified(tmp_path):
    import time

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

    created1, _, _ = collect(profile, "P", "out", incremental=True, root=tmp_path)
    assert len(created1) == 1

    time.sleep(0.01)
    fp.write_text("modified content that is longer")

    created2, _, _ = collect(profile, "P", "out", incremental=True, root=tmp_path)
    assert len(created2) == 1


def test_collect_incremental_detects_new_file(tmp_path):
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

    created1, _, _ = collect(profile, "P", "out", incremental=True, root=tmp_path)
    assert len(created1) == 1

    (src / "b.py").write_text("new file")

    created2, _, _ = collect(profile, "P", "out", incremental=True, root=tmp_path)
    assert len(created2) == 1
