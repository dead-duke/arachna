"""Tests for parallel I/O — workers, fallback, order preservation, edge cases."""

import os
from unittest.mock import patch

from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.collector import collect
from arachna.domain.collection.gatherer_strategies import _assemble_in_memory, _FullModeStrategy
from arachna.domain.tokenization.tokenizer import count_tokens


def _profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_parallel_io_fallback_sequential(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(5):
        (src / f"file_{i}.py").write_text(f"# file {i}\n")
    out = tmp_path / "out"
    out.mkdir()
    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "1"
    try:
        created, tokens_by_file, parts, metrics = collect(
            _profile(),
            "P",
            str(out),
            root=tmp_path,
        )
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]
    assert len(created) >= 1
    assert metrics.files_read == 5


def test_parallel_io_with_workers(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(10):
        (src / f"file_{i}.py").write_text(f"# file {i}\n")
    out = tmp_path / "out"
    out.mkdir()
    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "2"
    try:
        created, tokens_by_file, parts, metrics = collect(
            _profile(),
            "P",
            str(out),
            root=tmp_path,
        )
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]
    assert len(created) >= 1
    assert metrics.files_read == 10


def test_parallel_io_single_file(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "only.py").write_text("# only\n")
    out = tmp_path / "out"
    out.mkdir()
    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "4"
    try:
        created, tokens_by_file, parts, metrics = collect(
            _profile(),
            "P",
            str(out),
            root=tmp_path,
        )
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]
    assert len(created) == 1
    assert metrics.files_read == 1


def test_parallel_io_preserves_order(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(20):
        (src / f"file_{i:02d}.py").write_text(f"# file {i}\n")
    out = tmp_path / "out"
    out.mkdir()
    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "4"
    try:
        created, tokens_by_file, parts, metrics = collect(
            _profile(max_tokens=-1),
            "P",
            str(out),
            root=tmp_path,
        )
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]
    content = parts[0]
    idx_00 = content.index("file_00.py")
    idx_10 = content.index("file_10.py")
    idx_19 = content.index("file_19.py")
    assert idx_00 < idx_10 < idx_19


# Edge cases from gatherer_strategies


def test_full_mode_profile_files_dedup(tmp_path):
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
