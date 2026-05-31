import time

from arachna.gatherer import _collect_named_sections


def test_collect_sections_incremental_new_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.py").write_text("new file")
    sections, cache = _collect_named_sections(
        {"directories": [str(tmp_path)], "patterns": ["*.py"], "use_gitignore": False},
        exclude=[],
        incremental=True,
        cache={},
    )
    assert len(sections) == 1
    assert len(cache) > 0


def test_collect_sections_incremental_skips_unchanged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.py").write_text("unchanged")
    # First run
    sections1, cache = _collect_named_sections(
        {"directories": [str(tmp_path)], "patterns": ["*.py"], "use_gitignore": False},
        exclude=[],
        incremental=True,
        cache={},
    )
    assert len(sections1) == 1

    # Second run with same cache
    sections2, cache2 = _collect_named_sections(
        {"directories": [str(tmp_path)], "patterns": ["*.py"], "use_gitignore": False},
        exclude=[],
        incremental=True,
        cache=cache,
    )
    assert len(sections2) == 0


def test_collect_sections_incremental_detects_modified(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fp = tmp_path / "a.py"
    fp.write_text("original")
    # First run
    sections1, cache = _collect_named_sections(
        {"directories": [str(tmp_path)], "patterns": ["*.py"], "use_gitignore": False},
        exclude=[],
        incremental=True,
        cache={},
    )
    assert len(sections1) == 1

    # Modify file — ensure mtime changes on all platforms
    time.sleep(0.01)
    fp.write_text("modified")

    # Second run
    sections2, cache2 = _collect_named_sections(
        {"directories": [str(tmp_path)], "patterns": ["*.py"], "use_gitignore": False},
        exclude=[],
        incremental=True,
        cache=cache,
    )
    assert len(sections2) == 1
