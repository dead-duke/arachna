"""Edge case tests for gatherer_strategies.py uncovered branches."""

import os
from unittest.mock import patch

from arachna.domain.gatherer_strategies import _assemble_in_memory, _FullModeStrategy
from arachna.domain.tokenizer import count_tokens


def _profile(**kw):
    return {
        "directories": ["src"],
        "patterns": ["*.py"],
        "files": [],
        "exclude_patterns": [],
        "use_gitignore": False,
        "max_tokens": 16000,
        "split_mode": "by_file",
        **kw,
    }


def test_full_mode_profile_files_dedup(tmp_path):
    """profile files already in filepaths are not duplicated."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("code")
    (src / "utils.py").write_text("code")

    strategy = _FullModeStrategy()
    profile = _profile(files=[str(src / "main.py")])

    named, parts, indices, cache = strategy.assemble(
        profile,
        [],
        count_tokens,
        root=tmp_path,
        incremental=False,
        cache=None,
        verbose=False,
        query=None,
    )
    assert len(named) == 2


def test_full_mode_incremental_deleted(tmp_path):
    """Incremental mode reports deleted files."""
    src = tmp_path / "src"
    src.mkdir()
    f = src / "temp.py"
    f.write_text("code")

    strategy = _FullModeStrategy()
    profile = _profile()

    _, _, _, cache = strategy.assemble(
        profile,
        [],
        count_tokens,
        root=tmp_path,
        incremental=True,
        cache={},
        verbose=False,
        query=None,
    )
    f.unlink()

    named, parts, indices, cache2 = strategy.assemble(
        profile,
        [],
        count_tokens,
        root=tmp_path,
        incremental=True,
        cache=cache,
        verbose=False,
        query=None,
    )
    assert len(named) == 0


def test_full_mode_parallel_fallback_to_sequential(tmp_path):
    """When concurrent.futures import fails, falls back to sequential."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("code")
    (src / "extra.py").write_text("code")

    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "2"
    try:
        import sys

        with patch.dict(sys.modules, {"concurrent.futures": None}):
            strategy = _FullModeStrategy()
            profile = _profile()
            named, parts, indices, cache = strategy.assemble(
                profile,
                [],
                count_tokens,
                root=tmp_path,
                incremental=False,
                cache=None,
                verbose=False,
                query=None,
            )
            assert len(named) == 2
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]


def test_assemble_in_memory_unlimited_tokens(tmp_path):
    """_assemble_in_memory with max_tokens=-1 returns single part."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("code1")
    (src / "b.py").write_text("code2")

    profile = _profile(max_tokens=-1)
    named, parts, indices, cache = _assemble_in_memory(
        profile,
        [],
        count_tokens,
        root=tmp_path,
        incremental=False,
        cache=None,
        verbose=False,
        query=None,
        mode="repo-map",
        graph_cache={},
    )
    assert len(parts) == 1


def test_assemble_in_memory_verbose_compress_stats(tmp_path, capsys):
    """_assemble_in_memory with verbose and compress prints stats."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("a\n\n\n\nb\n")

    profile = _profile(compress=True, max_tokens=10)
    named, parts, indices, cache = _assemble_in_memory(
        profile,
        [],
        count_tokens,
        root=tmp_path,
        incremental=False,
        cache=None,
        verbose=True,
        query=None,
        mode="repo-map",
        graph_cache={},
    )
    captured = capsys.readouterr()
    assert "Compressed:" in captured.out
