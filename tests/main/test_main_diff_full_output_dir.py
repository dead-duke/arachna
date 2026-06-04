"""Tests for --diff --full with -o/--output-dir flag parsing (v1.6.2 coverage)."""

import json

from arachna.__main__ import _cmd_diff


def test_cmd_diff_full_with_o_flag(tmp_path, monkeypatch):
    """_cmd_diff --full with -o flag parses output-dir correctly."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("hello")
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 32768,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    from arachna.config import get_profile
    from arachna.watcher import create_snapshot

    create_snapshot(get_profile("code"), name="od-flag-test")

    custom_dir = tmp_path / "custom_o"
    custom_dir.mkdir(parents=True, exist_ok=True)

    _cmd_diff(
        [
            "arachna",
            "--diff",
            "--from",
            "od-flag-test",
            "--profile",
            "code",
            "--full",
            "-o",
            str(custom_dir),
        ]
    )

    files = list(custom_dir.glob("chat-diff-full*"))
    assert len(files) >= 1, f"No files in {custom_dir}, found: {list(custom_dir.iterdir())}"

    # Default dir should NOT have chat-diff-full files
    default_out = tmp_path / "out"
    default_files = list(default_out.glob("chat-diff-full*")) if default_out.exists() else []
    assert len(default_files) == 0


def test_cmd_diff_full_with_output_dir_long_flag(tmp_path, monkeypatch):
    """_cmd_diff --full with --output-dir flag parses correctly."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("hello")
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 32768,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    from arachna.config import get_profile
    from arachna.watcher import create_snapshot

    create_snapshot(get_profile("code"), name="od-long-test")

    custom_dir = tmp_path / "custom_long"
    custom_dir.mkdir(parents=True, exist_ok=True)

    _cmd_diff(
        [
            "arachna",
            "--diff",
            "--from",
            "od-long-test",
            "--profile",
            "code",
            "--full",
            "--output-dir",
            str(custom_dir),
        ]
    )

    files = list(custom_dir.glob("chat-diff-full*"))
    assert len(files) >= 1, f"No files in {custom_dir}"
