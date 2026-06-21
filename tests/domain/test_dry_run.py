from arachna.config.profile_config import ProfileConfig
from arachna.domain.gatherer import dry_run


def _profile(**overrides):
    p = ProfileConfig(
        name_template="chat",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=[str],
        patterns=["*.py"],
        use_gitignore=False,
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_single_file(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')")
    p = _profile(directories=[str(tmp_path)])
    stats = dry_run(p, root=tmp_path)
    assert stats["max_tokens"] == 16000
    assert len(stats["parts"]) == 1


def test_multiple_parts(tmp_path):
    (tmp_path / "a.py").write_text("x" * 500)
    (tmp_path / "b.py").write_text("y" * 500)
    p = _profile(directories=[str(tmp_path)], max_tokens=50)
    stats = dry_run(p, root=tmp_path)
    assert len(stats["parts"]) >= 4


def test_empty_dir(tmp_path):
    p = _profile(directories=[str(tmp_path)])
    stats = dry_run(p, root=tmp_path)
    assert len(stats["parts"]) == 0


def test_command_mode(tmp_path):
    p = ProfileConfig(
        name_template="chat",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_paragraph",
        command="echo hi",
        directories=[],
        patterns=[],
        use_gitignore=False,
    )
    stats = dry_run(p, root=tmp_path)
    assert len(stats["parts"]) == 1


def test_section_too_large(tmp_path):
    (tmp_path / "big.py").write_text("x" * 400)
    p = _profile(directories=[str(tmp_path)], max_tokens=10)
    stats = dry_run(p, root=tmp_path)
    assert len(stats["parts"]) >= 2
    assert stats["parts"][0]["total_tokens"] > 10
