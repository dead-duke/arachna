"""Tests for progress output to stderr."""

from arachna.collector import collect


def test_progress_stderr_large_collection(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(150):
        (src / f"file_{i}.py").write_text(f"# file {i}\n")

    out = tmp_path / "out"
    out.mkdir()

    collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 32000,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*.py"],
        },
        "P",
        str(out),
        verbose=True,
        root=tmp_path,
    )

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

    collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*.py"],
        },
        "P",
        str(out),
        verbose=True,
        root=tmp_path,
    )

    captured = capsys.readouterr()
    assert "Collecting..." not in captured.err
