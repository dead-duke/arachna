"""Integration tests for gitignore-based file exclusion."""

from pathlib import Path

from arachna.gatherer import gather_files


def test_gitignore_excludes_matched_files(tmp_path, monkeypatch):
    """Files matching .gitignore patterns are excluded from collection."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").write_text("*.txt\nsecret.key\n")
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "debug.txt").write_text("some log")
    (tmp_path / "secret.key").write_text("top secret")

    sections = gather_files(
        {
            "directories": [str(tmp_path)],
            "patterns": ["*"],
            "use_gitignore": True,
        }
    )
    # Only main.py should be collected
    filenames = [Path(s.split("\n")[0].replace("### ", "")).name for s in sections]
    assert "main.py" in filenames
    assert "debug.txt" not in filenames
    assert "secret.key" not in filenames


def test_gitignore_nested_patterns(tmp_path, monkeypatch):
    """Nested .gitignore patterns are respected — sub/.gitignore excludes nested files."""
    monkeypatch.chdir(tmp_path)
    # Root .gitignore excludes *.txt everywhere
    (tmp_path / ".gitignore").write_text("*.txt\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    # sub/.gitignore excludes *.csv in this subdirectory
    (sub / ".gitignore").write_text("*.csv\n")
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "debug.txt").write_text("root log")
    (sub / "nested.py").write_text("nested")
    (sub / "nested.csv").write_text("comma,separated")

    sections = gather_files(
        {
            "directories": [str(tmp_path)],
            "patterns": ["*"],
            "use_gitignore": True,
        }
    )
    filenames = [Path(s.split("\n")[0].replace("### ", "")).name for s in sections]
    # main.py and nested.py should be collected
    assert "main.py" in filenames
    assert "nested.py" in filenames
    # debug.txt excluded by root .gitignore
    assert "debug.txt" not in filenames
    # nested.csv excluded by sub/.gitignore
    assert "nested.csv" not in filenames


def test_gitignore_use_gitignore_false_includes_all(tmp_path, monkeypatch):
    """With use_gitignore=False, gitignored files are collected."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").write_text("*.txt\n")
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "debug.txt").write_text("some log")

    sections = gather_files(
        {
            "directories": [str(tmp_path)],
            "patterns": ["*"],
            "use_gitignore": False,
        }
    )
    filenames = [Path(s.split("\n")[0].replace("### ", "")).name for s in sections]
    assert "main.py" in filenames
    assert "debug.txt" in filenames


def test_gitignore_patterns_tracked_in_manifest(tmp_path, monkeypatch):
    """When .gitignore exists, gitignored files are excluded from collected content."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").write_text("*.txt\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / "src" / "debug.txt").write_text("log")

    from arachna.collector import collect

    created = collect(
        {
            "name_template": "chat-test",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*"],
            "use_gitignore": True,
        },
        "TestProject",
        "out",
    )
    # debug.txt should be excluded by .gitignore
    # main.py should be in the collected content
    assert len(created) == 1
    full = Path(created[0]).read_text()
    assert "main.py" in full
    assert "debug.txt" not in full
