"""Tests for gather_files — single, multiple, exclude, pre_commands, edge cases."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.gatherer import gather_files
from arachna.domain.collection.gatherer_files import (
    _collect_file_sections,
    _collect_named_sections,
    _format_one_file,
    _get_profile_files,
)
from arachna.domain.collection.gatherer_pre_commands import _collect_pre_commands
from arachna.domain.tokenization.tokenizer import count_tokens


def _profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=[],
        patterns=[],
        use_gitignore=False,
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_single():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "main.py").write_text("print('hello')")
        p = _profile(directories=[str(root)], patterns=["*.py"])
        sections = gather_files(p, root=root)
        assert len(sections) == 1
        assert "main.py" in sections[0]


def test_multiple():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "a.py").write_text("a")
        (root / "b.py").write_text("b")
        p = _profile(directories=[str(root)], patterns=["*.py"])
        sections = gather_files(p, root=root)
        assert len(sections) == 2


def test_exclude():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "main.py").write_text("ok")
        (root / "test.pyc").write_text("junk")
        p = _profile(directories=[str(root)], patterns=["*"], exclude_patterns=["*.pyc"])
        sections = gather_files(p, root=root)
        assert len(sections) == 1


def test_specific_files():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "README.md").write_text("# Hi")
        p = _profile(files=[str(root / "README.md")])
        sections = gather_files(p, root=root)
        assert len(sections) == 1


def test_nonexistent_file(tmp_path):
    p = _profile(files=["/nonexistent"])
    sections = gather_files(p, root=tmp_path)
    assert len(sections) == 0


def test_pre_commands(tmp_path):
    p = _profile(pre_commands=["echo hi"])
    sections = gather_files(p, root=tmp_path)
    assert len(sections) == 1


def test_empty_dir():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        p = _profile(directories=[str(root)], patterns=["*.py"])
        sections = gather_files(p, root=root)
        assert len(sections) == 0


def test_subdirectory():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "sub").mkdir()
        (root / "sub" / "nested.py").write_text("x")
        p = _profile(directories=[str(root)], patterns=["*.py"])
        sections = gather_files(p, root=root)
        assert len(sections) == 1


def test_collect_file_sections_not_found(tmp_path):
    p = _profile(files=["nonexistent.py"])
    sections = _collect_file_sections(p, [], count_tokens, root=tmp_path, verbose=False)
    assert len(sections) == 0


def test_collect_file_sections_excluded(tmp_path):
    f = tmp_path / "debug.log"
    f.write_text("log")
    p = _profile(files=[str(f)])
    sections = _collect_file_sections(p, ["*.log"], count_tokens, root=tmp_path, verbose=False)
    assert len(sections) == 0


def test_get_profile_files_not_a_file(tmp_path):
    (tmp_path / "subdir").mkdir()
    p = _profile(files=[str(tmp_path / "subdir")])
    files = _get_profile_files(p, [], root=tmp_path)
    assert len(files) == 0


def test_get_profile_files_excluded(tmp_path):
    f = tmp_path / "skip.me"
    f.write_text("skip")
    p = _profile(files=[str(f)])
    files = _get_profile_files(p, ["*.me"], root=tmp_path)
    assert len(files) == 0


def test_format_one_file_returns_none_for_binary(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = _format_one_file(f, "markdown", False, None, 1.0, False, False, False)
    assert result is None


def test_collect_named_sections_with_query(tmp_path):
    (tmp_path / "main.py").write_text("def login(): pass")
    (tmp_path / "utils.py").write_text("def helper(): pass")
    p = _profile(directories=[str(tmp_path)], patterns=["*.py"])
    sections, cache = _collect_named_sections(
        p,
        [],
        count_tokens,
        root=tmp_path,
        query="login",
    )
    names = [s[0] for s in sections]
    assert any("main.py" in n for n in names)
    assert not any("utils.py" in n for n in names)


def test_pre_command_long_label_is_truncated(tmp_path):
    long_cmd = "echo " + "x" * 60
    with patch("arachna.domain.collection.gatherer_pre_commands.run_pre_commands") as mock_run:
        mock_run.return_value = [(long_cmd, "output")]
        p = ProfileConfig(
            name_template="c",
            title_template="# T\n\n",
            max_tokens=16000,
            split_mode="by_file",
            directories=[],
            patterns=[],
            use_gitignore=False,
            pre_commands=[long_cmd],
        )
        result = _collect_pre_commands(p, count_tokens, root=tmp_path)
    assert len(result) == 1
    assert result[0][0].endswith("...")
