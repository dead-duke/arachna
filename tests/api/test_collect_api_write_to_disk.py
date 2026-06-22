"""Tests for write_to_disk param in collect_api."""

import json
from pathlib import Path

from arachna.api.collect_api import collect
from arachna.config.core.config import load_config
from arachna.config.profile_config import ProfileConfig


def test_collect_api_write_to_disk_false(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    config = load_config(root=tmp_path)
    profile = ProfileConfig(
        name_template="chat-test",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
    )
    result = collect(
        root=tmp_path, profile=profile, config=config, output_dir="out", write_to_disk=False
    )
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

    config = load_config(root=tmp_path)
    profile = ProfileConfig(
        name_template="chat-test",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
    )
    result = collect(
        root=tmp_path, profile=profile, config=config, output_dir="out", write_to_disk=True
    )
    assert len(result.parts) == 1
    assert len(result.files) == 1
    file_content = Path(result.files[0]).read_text()
    assert "main.py" in result.parts[0]
    assert "main.py" in file_content
    assert result.parts[0] in file_content
