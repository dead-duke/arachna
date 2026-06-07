"""Integration tests for merge + clean interaction."""

import json
from unittest.mock import patch

from arachna.__main__ import main


def test_merge_then_clean_removes_all(tmp_path, monkeypatch):
    """After merge with multiple runs, clean should remove all accumulated files."""
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 10}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x" * 200)
    (tmp_path / "src" / "b.py").write_text("y" * 200)

    # First merge run
    with patch("sys.argv", ["arachna", "--profile", "c", "--merge"]):
        main()
    files1 = sorted((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files1) >= 2

    # Second merge run
    with patch("sys.argv", ["arachna", "--profile", "c", "--merge"]):
        main()
    files2 = sorted((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files2) >= 4

    # Clean should remove all
    with patch("sys.argv", ["arachna", "--clean"]):
        main()
    files3 = list((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files3) == 0


def test_merge_then_all_cleans_globally(tmp_path, monkeypatch):
    """After merge, --all should clean old files and re-collect."""
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("print('hi')")

    # First merge run
    with patch("sys.argv", ["arachna", "--profile", "c", "--merge"]):
        main()
    files1 = sorted((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files1) == 1

    # Run --all (should clean old and create fresh)
    with patch("sys.argv", ["arachna", "--all"]):
        main()
    files2 = sorted((tmp_path / "arachna_context").glob("chat-c*.md"))
    # --all cleans all then recollects — should have exactly 1 file (single part)
    assert len(files2) == 1


def test_merge_single_part_sequential(tmp_path, monkeypatch):
    """Merge mode with single-file output increments correctly on each run."""
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("print('hi')")

    # Three merge runs
    for _ in range(3):
        with patch("sys.argv", ["arachna", "--profile", "c", "--merge"]):
            main()

    files = sorted((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files) == 3
    names = [f.name for f in files]
    assert "chat-c_1.md" in names
    assert "chat-c_2.md" in names
    assert "chat-c_3.md" in names


"""Tests for --profile X --merge CLI path (_cmd_single)."""


def test_merge_single_profile_cli(tmp_path, monkeypatch):
    """--profile X --merge appends to existing output."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}})
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("print('hi')")
    with patch("sys.argv", ["arachna", "--profile", "c", "--merge"]):
        main()
    files1 = sorted((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files1) == 1
    assert "chat-c_1.md" in str(files1[0])

    # Second merge run
    with patch("sys.argv", ["arachna", "--profile", "c", "--merge"]):
        main()
    files2 = sorted((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files2) == 2
    assert "chat-c_2.md" in str(files2[1])
