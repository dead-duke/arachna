from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.collector import collect


def _profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T (part {part})\n\n",
        max_tokens=-1,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_unlimited_single_part(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(10):
        (src / f"file_{i}.py").write_text(f"# file {i}\n" + "x" * 500)

    out = tmp_path / "out"
    out.mkdir()

    created, tokens_by_file, parts, metrics = collect(
        _profile(),
        "P",
        str(out),
        root=tmp_path,
    )

    assert len(parts) == 1
    assert len(created) == 1


def test_unlimited_all_files_present(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("a = 1")
    (src / "b.py").write_text("b = 2")

    out = tmp_path / "out"
    out.mkdir()

    created, tokens_by_file, parts, metrics = collect(
        _profile(),
        "P",
        str(out),
        root=tmp_path,
    )

    content = parts[0]
    assert "a.py" in content
    assert "b.py" in content
