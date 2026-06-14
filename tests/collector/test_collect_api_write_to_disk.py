"""Tests for write_to_disk param in collect_api (v2.9.2)."""

import json
from pathlib import Path

from arachna.collect_api import collect


def _make_profile() -> dict:
    return {
        "name_template": "chat-test",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }


def test_collect_api_write_to_disk_false(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    import os

    os.chdir(tmp_path)
    result = collect(profile=_make_profile(), output_dir="out", write_to_disk=False)
    assert len(result.parts) == 1
    assert "main.py" in result.parts[0]
    assert result.files == []


def test_collect_api_parts_match_files(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    import os

    os.chdir(tmp_path)
    result = collect(profile=_make_profile(), output_dir="out", write_to_disk=True)
    assert len(result.parts) == 1
    assert len(result.files) == 1
    file_content = Path(result.files[0]).read_text()
    assert "main.py" in result.parts[0]
    assert "main.py" in file_content
    assert result.parts[0] in file_content
