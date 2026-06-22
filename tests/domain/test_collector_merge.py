"""Additional coverage for collector.py — merge lock, clean_manifest, _build_toc."""

from pathlib import Path
from unittest.mock import patch

from arachna.domain.collection.collector import (
    _build_toc,
    _get_lock_functions,
    clean_manifest,
    save_manifest,
)
from arachna.domain.path_utils import SafePath


def _safe_out(tmp_path, name="out"):
    out = tmp_path / name
    out.mkdir(exist_ok=True)
    return SafePath(out, tmp_path)


def test_merge_lock_no_fcntl_no_msvcrt(tmp_path):
    """_merge_lock with fallback O_CREAT|O_EXCL lock."""
    import sys

    with patch.dict(sys.modules, {"fcntl": None, "msvcrt": None}):
        _get_lock_functions.cache_clear()
        try:
            from arachna.domain.collection.collector import _merge_lock

            out = _safe_out(tmp_path)
            with _merge_lock(out):
                (Path(str(out)) / "test.txt").write_text("locked")

            assert not (Path(str(out)) / ".arachna_merge.lock").exists()
        finally:
            _get_lock_functions.cache_clear()


def test_clean_manifest_empty_name_tmpl(tmp_path):
    """clean_manifest with empty name_tmpl removes all tracked files."""
    out = _safe_out(tmp_path)
    (Path(str(out)) / "chat-c_1.md").write_text("x")
    (Path(str(out)) / "chat-d.md").write_text("y")
    save_manifest(out, ["chat-c_1.md", "chat-d.md"])

    clean_manifest(out, "")

    assert not (Path(str(out)) / "chat-c_1.md").exists()
    assert not (Path(str(out)) / "chat-d.md").exists()


def test_clean_manifest_plain_file(tmp_path):
    """clean_manifest removes plain (non-numbered) file."""
    out = _safe_out(tmp_path)
    (Path(str(out)) / "chat-c.md").write_text("x")
    (Path(str(out)) / "chat-c_1.md").write_text("y")
    save_manifest(out, ["chat-c.md", "chat-c_1.md"])

    clean_manifest(out, "chat-c")

    assert not (Path(str(out)) / "chat-c.md").exists()
    assert not (Path(str(out)) / "chat-c_1.md").exists()


def test_clean_manifest_nonexistent_files(tmp_path):
    """clean_manifest handles non-existent files gracefully."""
    out = _safe_out(tmp_path)
    save_manifest(out, ["chat-gone.md"])

    clean_manifest(out, "chat")


def test_build_toc_pre_commands_label(tmp_path):
    """_build_toc includes pre: label as-is."""
    sections = [
        ("pre: tree -I '*.pyc' src", "tree output", 5),
        ("src/main.py", "### src/main.py\n\n```python\ncode\n```\n", 10),
    ]
    toc = _build_toc(sections, [0, 1], 1, 2)
    assert "pre: tree" in toc
    assert "main.py" in toc


def test_build_toc_windows_path(tmp_path):
    """_build_toc handles Windows backslash paths."""
    sections = [
        ("src\\main.py", "content", 10),
    ]
    toc = _build_toc(sections, [0], 1, 1)
    assert "main.py" in toc


def test_build_toc_out_of_range_index(tmp_path):
    """_build_toc with out-of-range index is safe."""
    sections = [("src/main.py", "content", 10)]
    toc = _build_toc(sections, [0, 5, 10], 1, 1)
    assert "main.py" in toc
