from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.collector import collect


def _profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T (part {part})\n\n",
        max_tokens=32000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_progress_stderr_large_collection(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(150):
        (src / f"file_{i}.py").write_text(f"# file {i}\n")

    out = tmp_path / "out"
    out.mkdir()

    collect(_profile(max_tokens=32000), "P", str(out), verbose=True, root=tmp_path)

    captured = capsys.readouterr()
    assert "Collecting..." in captured.err
    assert "collected 100/" in captured.err


def test_no_progress_small_collection(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(5):
        (src / f"file_{i}.py").write_text(f"# file {i}\n")

    out = tmp_path / "out"
    out.mkdir()

    collect(_profile(), "P", str(out), verbose=True, root=tmp_path)

    captured = capsys.readouterr()
    assert "Collecting..." not in captured.err
