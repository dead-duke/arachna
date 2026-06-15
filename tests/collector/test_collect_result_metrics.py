"""Tests for CollectResult.metrics field."""

import json

from arachna.collect_api import collect


def test_collect_result_has_metrics(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    import os

    os.chdir(tmp_path)

    result = collect(
        profile={
            "name_template": "chat-api",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*.py"],
            "use_gitignore": False,
        },
        output_dir="out",
    )

    assert result.metrics is not None
    assert result.metrics.files_read >= 1
    assert result.metrics.tokens_raw > 0
    assert result.metrics.extract_time_ms >= 0
    assert result.metrics.load_time_ms >= 0


def test_collect_result_metrics_empty(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    (tmp_path / "empty").mkdir()

    import os

    os.chdir(tmp_path)

    result = collect(
        profile={
            "name_template": "chat-api",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_file",
            "directories": ["empty"],
            "patterns": ["*.py"],
            "use_gitignore": False,
        },
        output_dir="out",
    )

    assert result.metrics is not None
    assert result.metrics.files_read == 0
