"""Integration tests for v3.0 CLI — collect/diff gaps."""

import json

from tests.integration.conftest import _arachna


def test_collect_no_pre_commands(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                        "pre_commands": ["echo 'PRE OUTPUT'"],
                    }
                },
            }
        )
    )

    result = _arachna("collect", "--profile", "code", "--no-pre-commands", cwd=tmp_path)
    assert result.returncode == 0

    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "main.py" in content
    assert "PRE OUTPUT" not in content


def test_diff_to_cross_snapshot_cli(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("v1")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    _arachna("snapshot", "create", "--profile", "code", "--name", "v1-snap", cwd=tmp_path)
    (tmp_path / "src" / "main.py").write_text("v2")
    _arachna("snapshot", "create", "--profile", "code", "--name", "v2-snap", cwd=tmp_path)

    result = _arachna("diff", "--from", "v1-snap", "--to", "v2-snap", cwd=tmp_path)
    assert result.returncode == 0

    files = list(out_dir.glob("chat-diff-v1-snap-to-v2-snap*"))
    assert len(files) >= 1


def test_diff_all_compress_cli(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("a\n\n\n\nb\n")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    result = _arachna("diff", "--all", "--profile", "code", "--compress", cwd=tmp_path)
    assert result.returncode == 0

    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "\n\n\n\n" not in content


def test_diff_format_xml_cli(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    _arachna("snapshot", "create", "--profile", "code", "--name", "xml-snap", cwd=tmp_path)
    (tmp_path / "src" / "main.py").write_text("modified")

    result = _arachna(
        "diff", "--from", "xml-snap", "--profile", "code", "--format", "xml", cwd=tmp_path
    )
    assert result.returncode == 0

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert 'file path="' in content


def test_snapshot_update_with_profile_cli(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    },
                    "alt": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    },
                },
            }
        )
    )

    _arachna("snapshot", "create", "--profile", "code", "--name", "upd-prof-cli", cwd=tmp_path)
    result = _arachna("snapshot", "update", "upd-prof-cli", "--profile", "alt", cwd=tmp_path)
    assert result.returncode == 0
    assert "updated" in result.stdout


def test_collect_mode_headers_cli(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import os\n\ndef foo():\n    return 1\n")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    result = _arachna("collect", "--profile", "code", "--mode", "headers", cwd=tmp_path)
    assert result.returncode == 0

    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "deps:" in content
    assert "exports:" in content


def test_collect_mode_repo_map_cli(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def foo():\n    return 1\n\nclass Bar:\n    pass\n")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    result = _arachna("collect", "--profile", "code", "--mode", "repo-map", cwd=tmp_path)
    assert result.returncode == 0

    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content
    assert "class Bar:" in content
    assert "return 1" not in content
