import time

from arachna.domain.gatherer_core import _collect_named_sections
from arachna.domain.tokenizer import count_tokens


def test_collect_sections_incremental_new_files(tmp_path):
    (tmp_path / "a.py").write_text("new file")
    sections, cache = _collect_named_sections(
        {"directories": [str(tmp_path)], "patterns": ["*.py"], "use_gitignore": False},
        exclude=[],
        tokenizer=count_tokens,
        incremental=True,
        cache={},
        root=tmp_path,
    )
    assert len(sections) == 1
    assert len(cache) > 0


def test_collect_sections_incremental_skips_unchanged(tmp_path):
    (tmp_path / "a.py").write_text("unchanged")
    sections1, cache = _collect_named_sections(
        {"directories": [str(tmp_path)], "patterns": ["*.py"], "use_gitignore": False},
        exclude=[],
        tokenizer=count_tokens,
        incremental=True,
        cache={},
        root=tmp_path,
    )
    assert len(sections1) == 1

    sections2, cache2 = _collect_named_sections(
        {"directories": [str(tmp_path)], "patterns": ["*.py"], "use_gitignore": False},
        exclude=[],
        tokenizer=count_tokens,
        incremental=True,
        cache=cache,
        root=tmp_path,
    )
    assert len(sections2) == 0


def test_collect_sections_incremental_detects_modified(tmp_path):
    fp = tmp_path / "a.py"
    fp.write_text("original")
    sections1, cache = _collect_named_sections(
        {"directories": [str(tmp_path)], "patterns": ["*.py"], "use_gitignore": False},
        exclude=[],
        tokenizer=count_tokens,
        incremental=True,
        cache={},
        root=tmp_path,
    )
    assert len(sections1) == 1

    time.sleep(0.01)
    fp.write_text("modified")

    sections2, cache2 = _collect_named_sections(
        {"directories": [str(tmp_path)], "patterns": ["*.py"], "use_gitignore": False},
        exclude=[],
        tokenizer=count_tokens,
        incremental=True,
        cache=cache,
        root=tmp_path,
    )
    assert len(sections2) == 1
