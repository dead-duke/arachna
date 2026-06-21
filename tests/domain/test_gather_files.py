import tempfile
from pathlib import Path

from arachna.config.profile_config import ProfileConfig
from arachna.domain.gatherer import gather_files


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
