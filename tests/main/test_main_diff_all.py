"""Tests for diff --all CLI handler — updated for v3.4.0."""

import json

from arachna.cli.diff import _cmd_diff_all


def _make_args(profile="code", mode=None, query=None, compress=False, output_dir=None):
    from argparse import Namespace

    return Namespace(
        profile=profile, mode=mode, query=query, compress=compress, output_dir=output_dir
    )


def test_cmd_diff_all_full(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_diff_all(_make_args(), config)

    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "main.py" in content


def test_cmd_diff_all_repo_map_mode(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n\ndef bar():\n    return 2\n")
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_diff_all(_make_args(mode="repo-map"), config)

    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content
    assert "def bar():" in content
    assert "return 1" not in content


def test_cmd_diff_all_with_query(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass")
    (src / "utils.py").write_text("def helper(): pass")
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_diff_all(_make_args(query="auth"), config)

    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "auth.py" in content
    assert "utils.py" not in content


def test_cmd_diff_all_with_compress(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("a\n\n\n\nb\n")
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_diff_all(_make_args(compress=True), config)

    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "\n\n\n\n" not in content


def test_cmd_diff_all_empty_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty").mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["empty"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    config = json.loads((tmp_path / ".arachna.json").read_text())
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff_all(_make_args(), config)
    sys.stdout = old
    assert "No content collected" in out.getvalue()


def test_cmd_diff_all_custom_output_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    custom_dir = tmp_path / "custom"
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_diff_all(_make_args(output_dir=str(custom_dir)), config)

    files = list(custom_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
