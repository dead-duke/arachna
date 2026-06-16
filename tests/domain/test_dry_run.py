from arachna.domain.gatherer import dry_run


def test_single_file(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')")
    stats = dry_run(
        {
            "directories": [str(tmp_path)],
            "patterns": ["*.py"],
            "max_tokens": 16000,
            "name_template": "chat",
        },
        root=tmp_path,
    )
    assert stats["max_tokens"] == 16000
    assert len(stats["parts"]) == 1


def test_multiple_parts(tmp_path):
    (tmp_path / "a.py").write_text("x" * 500)
    (tmp_path / "b.py").write_text("y" * 500)
    stats = dry_run(
        {
            "directories": [str(tmp_path)],
            "patterns": ["*.py"],
            "max_tokens": 50,
            "name_template": "chat",
        },
        root=tmp_path,
    )
    assert len(stats["parts"]) >= 4


def test_empty_dir(tmp_path):
    stats = dry_run(
        {
            "directories": [str(tmp_path)],
            "patterns": ["*.py"],
            "max_tokens": 16000,
            "name_template": "chat",
        },
        root=tmp_path,
    )
    assert len(stats["parts"]) == 0


def test_command_mode(tmp_path):
    stats = dry_run(
        {"command": "echo hi", "max_tokens": 16000, "name_template": "chat"}, root=tmp_path
    )
    assert len(stats["parts"]) == 1


def test_section_too_large(tmp_path):
    (tmp_path / "big.py").write_text("x" * 400)
    stats = dry_run(
        {
            "directories": [str(tmp_path)],
            "patterns": ["*.py"],
            "max_tokens": 10,
            "name_template": "chat",
        },
        root=tmp_path,
    )
    assert len(stats["parts"]) >= 2
    assert stats["parts"][0]["total_tokens"] > 10
