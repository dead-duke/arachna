"""Edge cases for progress to stderr."""

from arachna.domain.collector import collect


def _profile(**kw):
    return {
        "name_template": "c",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
        **kw,
    }


def test_progress_not_printed_without_verbose(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(150):
        (src / f"file_{i}.py").write_text(f"# {i}")
    out = tmp_path / "out"
    out.mkdir()

    collect(_profile(), "P", str(out), root=tmp_path, verbose=False)
    captured = capsys.readouterr()
    assert "Collecting..." not in captured.err
    assert "collected 100/" not in captured.err


def test_progress_not_printed_small_collection(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(5):
        (src / f"file_{i}.py").write_text(f"# {i}")
    out = tmp_path / "out"
    out.mkdir()

    collect(_profile(), "P", str(out), root=tmp_path, verbose=True)
    captured = capsys.readouterr()
    assert "Collecting..." not in captured.err


def test_progress_printed_large_collection(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(150):
        (src / f"file_{i}.py").write_text(f"# {i}")
    out = tmp_path / "out"
    out.mkdir()

    collect(_profile(), "P", str(out), root=tmp_path, verbose=True)
    captured = capsys.readouterr()
    assert "Collecting..." in captured.err
    assert "collected 100/" in captured.err
