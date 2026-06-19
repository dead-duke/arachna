from pathlib import Path
from unittest.mock import patch

from arachna.domain.collector import (
    _find_next_part_num,
    clean_manifest,
    collect,
    load_manifest,
    save_manifest,
)
from arachna.domain.path_utils import SafePath


def _safe_out(tmp_path, name="out"):
    out = tmp_path / name
    out.mkdir(exist_ok=True)
    return SafePath(out, tmp_path)


def test_single_file(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    out = tmp_path / "single_out"
    out.mkdir()
    created, tokens_by_file, _parts, _metrics = collect(
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
        root=tmp_path,
    )
    assert len(created) == 1
    assert "c_1.md" in created[0]


def test_multiple_parts(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x" * 2000)
    (src / "b.py").write_text("y" * 2000)
    out = tmp_path / "multi_out"
    out.mkdir()
    created, tokens_by_file, _parts, _metrics = collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 10,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*.py"],
        },
        "P",
        str(out),
        root=tmp_path,
    )
    assert len(created) >= 4


def test_empty(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "empty_out"
    out.mkdir()
    created, tokens_by_file, _parts, _metrics = collect(
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
        root=tmp_path,
    )
    assert len(created) == 0


def test_command_mode(tmp_path):
    out = tmp_path / "cmd_out"
    out.mkdir()
    created, tokens_by_file, _parts, _metrics = collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_paragraph",
            "command": "echo hi",
        },
        "P",
        str(out),
        root=tmp_path,
    )
    assert len(created) == 1


def test_merge_mode_single_part(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("print('hi')")
    out = tmp_path / "merge_single_out"
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

    created1, _, _, _ = collect(profile, "P", str(out), merge=True, root=tmp_path)
    assert len(created1) == 1
    assert "c_1.md" in created1[0]

    created2, _, _, _ = collect(profile, "P", str(out), merge=True, root=tmp_path)
    assert len(created2) == 1
    assert "c_2.md" in created2[0]


def test_merge_mode_multiple_parts(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x" * 2000)
    (src / "b.py").write_text("y" * 2000)
    out = tmp_path / "merge_multi_out"
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

    created1, _, _, _ = collect(profile, "P", str(out), merge=True, root=tmp_path)
    assert len(created1) >= 4
    assert any("c_1.md" in f for f in created1)

    created2, _, _, _ = collect(profile, "P", str(out), merge=True, root=tmp_path)
    assert len(created2) >= 4


def test_save_and_load_manifest(tmp_path):
    out = _safe_out(tmp_path, "manifest_out")
    save_manifest(out, ["a.md", "b.md"])
    loaded = load_manifest(out)
    assert loaded == ["a.md", "b.md"]


def test_load_manifest_empty(tmp_path):
    out = _safe_out(tmp_path, "load_empty_out")
    assert load_manifest(out) == []


def test_load_manifest_corrupted(tmp_path):
    out = tmp_path / "corrupt_out"
    out.mkdir()
    (out / ".arachna_manifest.json").write_text("not json")
    assert load_manifest(SafePath(out, tmp_path)) == []


def test_clean_manifest(tmp_path):
    out = _safe_out(tmp_path, "clean_out")
    (Path(str(out)) / "chat-c_1.md").write_text("x")
    (Path(str(out)) / "chat-c.md").write_text("x")
    save_manifest(out, ["chat-c_1.md", "chat-c.md"])

    clean_manifest(out, "chat-c")
    assert not (Path(str(out)) / "chat-c_1.md").exists()
    assert not (Path(str(out)) / "chat-c.md").exists()


def test_find_next_part_num_empty(tmp_path):
    out = _safe_out(tmp_path, "find_empty_out")
    assert _find_next_part_num(out, "chat-c") == 1


def test_find_next_part_num_existing(tmp_path):
    out = _safe_out(tmp_path, "find_existing_out")
    (Path(str(out)) / "chat-c_1.md").write_text("x")
    (Path(str(out)) / "chat-c_2.md").write_text("x")
    assert _find_next_part_num(out, "chat-c") == 3


def test_find_next_part_num_single_file(tmp_path):
    out = _safe_out(tmp_path, "find_single_out")
    (Path(str(out)) / "chat-c.md").write_text("x")
    assert _find_next_part_num(out, "chat-c") == 2


def test_find_next_part_num_mixed(tmp_path):
    out = _safe_out(tmp_path, "find_mixed_out")
    (Path(str(out)) / "chat-c.md").write_text("x")
    (Path(str(out)) / "chat-c_3.md").write_text("x")
    assert _find_next_part_num(out, "chat-c") == 4


def test_post_commands_executed(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    out = tmp_path / "post_out"
    out.mkdir()

    with patch("arachna.domain.collector.run_command") as mock_run:
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
            str(out),
            root=tmp_path,
        )
        mock_run.assert_called_with("echo done", root=tmp_path, allow_file_args=True)


def test_metrics_written(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    out = tmp_path / "metrics_out"
    out.mkdir()
    created, tokens_by_file, parts, metrics = collect(
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
        root=tmp_path,
    )
    assert metrics is not None
    assert metrics.files_read >= 1
    assert metrics.extract_time_ms >= 0
    assert metrics.load_time_ms >= 0
    assert metrics.tokens_raw > 0
    assert metrics.tokens_compressed > 0
    metrics_file = out / ".arachna_metrics.json"
    assert metrics_file.exists()
    import json

    data = json.loads(metrics_file.read_text())
    assert data["files_read"] >= 1
