from arachna.collector import collect


def test_single_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    out = tmp_path / "out"
    out.mkdir()
    created = collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*.py"],
        },
        "P",
        "out",
    )
    assert len(created) == 1
    assert "c.md" in created[0]


def test_multiple_parts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x" * 2000)
    (src / "b.py").write_text("y" * 2000)
    out = tmp_path / "out"
    out.mkdir()
    created = collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 10,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*.py"],
        },
        "P",
        "out",
    )
    assert len(created) == 2


def test_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"
    out.mkdir()
    created = collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*.py"],
        },
        "P",
        "out",
    )
    assert len(created) == 0


def test_command_mode(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    created = collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_paragraph",
            "command": "echo hi",
        },
        "P",
        "out",
    )
    assert len(created) == 1
