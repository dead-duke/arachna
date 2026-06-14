"""Coverage for Watch CLI handlers — updated for v3.4.0."""

import json
import sys
from io import StringIO

from arachna.cli.diff import _cmd_diff
from arachna.cli.snapshot import (
    _cmd_snapshot_create,
    _cmd_snapshot_info,
    _cmd_snapshot_update,
)


def test_cmd_diff_format_xml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    args = _make_diff_args(from_snapshot=None, profile="code", fmt="xml")
    _cmd_snapshot_create(_make_snap_create_args("xml-test", "code"), config)
    (tmp_path / "src" / "main.py").write_text("modified for xml")

    args = _make_diff_args(from_snapshot="xml-test", profile="code", fmt="xml")
    _cmd_diff(args, config)

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert 'file path="' in content


def test_cmd_diff_mode_structural(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def foo():\n    return 1\n")
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
    _cmd_snapshot_create(_make_snap_create_args("struct-cov", "code"), config)
    (tmp_path / "src" / "main.py").write_text("def foo():\n    return 2\n")

    args = _make_diff_args(from_snapshot="struct-cov", profile="code", mode="structural")
    _cmd_diff(args, config)

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "MODIFIED" in content or "modified" in content.lower()


def test_cmd_diff_mode_repo_map(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text(
        "def foo():\n    return 1\n\ndef bar():\n    return 2\n"
    )
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
    _cmd_snapshot_create(_make_snap_create_args("rm-cov", "code"), config)
    (tmp_path / "src" / "main.py").write_text(
        "def foo():\n    return 3\n\ndef bar():\n    return 4\n"
    )

    args = _make_diff_args(from_snapshot="rm-cov", profile="code", mode="repo-map")
    _cmd_diff(args, config)

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content


def test_cmd_diff_compress(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original\n\n\n\nspaces")
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
    _cmd_snapshot_create(_make_snap_create_args("comp-cov", "code"), config)
    (tmp_path / "src" / "main.py").write_text("modified\n\n\n\nafter")

    args = _make_diff_args(from_snapshot="comp-cov", profile="code", compress=True)
    _cmd_diff(args, config)

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1


def test_cmd_snapshot_info_full_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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
                        "pre_commands": ["echo hello"],
                    }
                },
            }
        )
    )

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("info-full", "code"), config)

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_info(_make_snap_info_args("info-full"), config)
    sys.stdout = old

    output = out.getvalue()
    assert "Snapshot: info-full" in output
    assert "Created:" in output
    assert "Files:" in output
    assert "Pre-commands:" in output
    assert "Profile:" in output


def test_cmd_snapshot_update_with_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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
                    }
                },
            }
        )
    )

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("upd-cov", "code"), config)

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_update(_make_snap_update_args("upd-cov", "code"), config)
    sys.stdout = old

    assert "updated" in out.getvalue()


def test_cmd_diff_stat_only_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original")
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
    _cmd_snapshot_create(_make_snap_create_args("stat-cov", "code"), config)
    (tmp_path / "src" / "main.py").write_text("modified v2")

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_make_diff_args(from_snapshot="stat-cov", profile="code", stat=True), config)
    sys.stdout = old

    output = out.getvalue()
    assert "Modified:" in output
    assert "Added:" in output
    assert "Deleted:" in output
    assert "Tokens:" in output


def test_cmd_diff_flat_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("flat-cov", "code"), config)
    (tmp_path / "src" / "main.py").write_text("modified flat")

    _cmd_diff(_make_diff_args(from_snapshot="flat-cov", profile="code", flat=True), config)

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1


# ── helpers ────────────────────────────────────────────────────────


def _make_snap_create_args(name, profile):
    from argparse import Namespace

    return Namespace(name=name, profile=profile)


def _make_snap_update_args(sid, profile=None):
    from argparse import Namespace

    return Namespace(id=sid, profile=profile)


def _make_snap_info_args(sid, profile_only=False, stats_only=False):
    from argparse import Namespace

    return Namespace(id=sid, profile_only=profile_only, stats_only=stats_only)


def _make_diff_args(
    from_snapshot=None,
    to=None,
    all=False,
    profile=None,
    stat=False,
    flat=False,
    fmt=None,
    mode=None,
    compress=False,
    output_dir=None,
    query=None,
):
    from argparse import Namespace

    return Namespace(
        from_snapshot=from_snapshot,
        to=to,
        all=all,
        profile=profile,
        stat=stat,
        flat=flat,
        format=fmt,
        mode=mode,
        compress=compress,
        output_dir=output_dir,
        query=query,
    )
