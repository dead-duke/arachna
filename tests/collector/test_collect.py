from unittest.mock import patch

from arachna.collector import (
    _find_next_part_num,
    clean_manifest,
    collect,
    load_manifest,
    save_manifest,
)


def test_single_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    out = tmp_path / "out"
    out.mkdir()
    created, tokens_by_file, _parts = collect(
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
    assert "c_1.md" in created[0]


def test_multiple_parts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x" * 2000)
    (src / "b.py").write_text("y" * 2000)
    out = tmp_path / "out"
    out.mkdir()
    created, tokens_by_file, _parts = collect(
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
    # 2 files, each oversized -> split into chunks, >= 4 parts total
    assert len(created) >= 4


def test_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"
    out.mkdir()
    created, tokens_by_file, _parts = collect(
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
    created, tokens_by_file, _parts = collect(
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


def test_merge_mode_single_part(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("print('hi')")
    out = tmp_path / "out"
    out.mkdir()

    profile = {
        "name_template": "c",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    created1, _, _ = collect(profile, "P", "out", merge=True)
    assert len(created1) == 1
    assert "c_1.md" in created1[0]

    created2, _, _ = collect(profile, "P", "out", merge=True)
    assert len(created2) == 1
    assert "c_2.md" in created2[0]


def test_merge_mode_multiple_parts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x" * 2000)
    (src / "b.py").write_text("y" * 2000)
    out = tmp_path / "out"
    out.mkdir()

    profile = {
        "name_template": "c",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 10,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }

    created1, _, _ = collect(profile, "P", "out", merge=True)
    # 2 files, each oversized -> split into chunks, >= 4 parts total
    assert len(created1) >= 4
    assert any("c_1.md" in f for f in created1)

    created2, _, _ = collect(profile, "P", "out", merge=True)
    assert len(created2) >= 4


def test_save_and_load_manifest(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    save_manifest(out, ["a.md", "b.md"])
    loaded = load_manifest(out)
    assert loaded == ["a.md", "b.md"]


def test_load_manifest_empty(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    assert load_manifest(out) == []


def test_load_manifest_corrupted(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / ".arachna_manifest.json").write_text("not json")
    assert load_manifest(out) == []


def test_clean_manifest(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "chat-c_1.md").write_text("x")
    (out / "chat-c.md").write_text("x")
    save_manifest(out, ["chat-c_1.md", "chat-c.md"])

    clean_manifest(out, "chat-c")
    assert not (out / "chat-c_1.md").exists()
    assert not (out / "chat-c.md").exists()


def test_find_next_part_num_empty(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    assert _find_next_part_num(out, "chat-c") == 1


def test_find_next_part_num_existing(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "chat-c_1.md").write_text("x")
    (out / "chat-c_2.md").write_text("x")
    assert _find_next_part_num(out, "chat-c") == 3


def test_find_next_part_num_single_file(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "chat-c.md").write_text("x")
    assert _find_next_part_num(out, "chat-c") == 2


def test_find_next_part_num_mixed(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "chat-c.md").write_text("x")
    (out / "chat-c_3.md").write_text("x")
    assert _find_next_part_num(out, "chat-c") == 4


def test_post_commands_executed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    out = tmp_path / "out"
    out.mkdir()

    with patch("arachna.collector.run_command") as mock_run:
        mock_run.return_value = "done"
        collect(
            {
                "name_template": "c",
                "title_template": "# T (part {part})\n\n",
                "max_tokens": 16000,
                "split_mode": "by_file",
                "directories": ["src"],
                "patterns": ["*.py"],
                "use_gitignore": False,
                "post_commands": ["echo done"],
            },
            "P",
            "out",
        )
        mock_run.assert_called_with("echo done", allow_file_args=True)
