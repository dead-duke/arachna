from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.collector import collect
from arachna.domain.collection.gatherer import dry_run
from arachna.domain.execution.splitter import split


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


def test_unlimited_split_by_file(tmp_path):
    content = "### a.py\n\n```python\ncode\n```\n\n### b.py\n\n```python\ncode\n```"
    parts = split(content, -1, mode="by_file")
    assert len(parts) == 1
    assert "a.py" in parts[0]
    assert "b.py" in parts[0]


def test_unlimited_split_by_paragraph(tmp_path):
    parts = split("para1\n\npara2\n\npara3", -1, mode="by_paragraph")
    assert len(parts) == 1


def test_unlimited_split_single(tmp_path):
    parts = split("hello world", -1, mode="single")
    assert len(parts) == 1
    assert "hello world" in parts[0]


def test_unlimited_dry_run(tmp_path):
    (tmp_path / "a.py").write_text("x" * 500)
    (tmp_path / "b.py").write_text("y" * 500)
    p = _profile(directories=[str(tmp_path)], max_tokens=-1)
    stats = dry_run(p, root=tmp_path)
    assert len(stats["parts"]) == 1


def test_unlimited_collect_single_part(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(10):
        (src / f"file_{i}.py").write_text(f"# file {i}\n" + "x" * 500)
    out = tmp_path / "out"
    out.mkdir()

    created, tokens_by_file, parts, metrics = collect(
        _profile(max_tokens=-1),
        "P",
        str(out),
        root=tmp_path,
    )
    assert len(parts) == 1
    assert len(created) == 1


def test_unlimited_collect_with_query(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass")
    (src / "utils.py").write_text("def helper(): pass")
    out = tmp_path / "out"
    out.mkdir()

    _, _, parts, _ = collect(
        _profile(max_tokens=-1),
        "P",
        str(out),
        root=tmp_path,
        query="auth",
    )
    assert len(parts) == 1
    assert "auth.py" in parts[0]
    assert "utils.py" not in parts[0]


def test_unlimited_collect_with_merge(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x = 1")
    out = tmp_path / "out"
    out.mkdir()

    profile = _profile(max_tokens=-1)
    c1, _, _, _ = collect(profile, "P", str(out), root=tmp_path, merge=True)
    c2, _, _, _ = collect(profile, "P", str(out), root=tmp_path, merge=True)
    assert len(c1) == 1
    assert len(c2) == 1
    assert "c_1.md" in c1[0]
    assert "c_2.md" in c2[0]
