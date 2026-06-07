"""Coverage for cli_watch.py — uncovered branches (v2.5.0)."""

import json
import sys
from io import StringIO

import pytest

from arachna.cli_watch import _cmd_diff, _cmd_snapshot

# ── _cmd_diff --format xml ────────────────────────────────────────


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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "xml-test"])
    (tmp_path / "src" / "main.py").write_text("modified for xml")

    _cmd_diff(["arachna", "--diff", "--from", "xml-test", "--profile", "code", "--format", "xml"])

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert 'file path="' in content


# ── _cmd_diff --mode structural ───────────────────────────────────


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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "struct-cov"])
    (tmp_path / "src" / "main.py").write_text("def foo():\n    return 2\n")

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(
        [
            "arachna",
            "--diff",
            "--from",
            "struct-cov",
            "--profile",
            "code",
            "--mode",
            "structural",
        ]
    )
    sys.stdout = old

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "MODIFIED" in content or "modified" in content.lower()


# ── _cmd_diff --mode repo-map ─────────────────────────────────────


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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "rm-cov"])
    (tmp_path / "src" / "main.py").write_text(
        "def foo():\n    return 3\n\ndef bar():\n    return 4\n"
    )

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "rm-cov", "--profile", "code", "--mode", "repo-map"])
    sys.stdout = old

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content


# ── _cmd_diff --compress ──────────────────────────────────────────


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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "comp-cov"])
    (tmp_path / "src" / "main.py").write_text("modified\n\n\n\nafter")

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "comp-cov", "--profile", "code", "--compress"])
    sys.stdout = old

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1


# ── _cmd_diff_all with query ──────────────────────────────────────


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

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--all", "--profile", "code", "--query", "auth"])
    sys.stdout = old

    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "auth.py" in content
    assert "utils.py" not in content


# ── _cmd_diff_all with compress ───────────────────────────────────


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

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--all", "--profile", "code", "--compress"])
    sys.stdout = old

    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "\n\n\n\n" not in content


# ── _cmd_diff_all with -o flag ────────────────────────────────────


def test_cmd_diff_all_with_short_o_flag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    custom_dir = tmp_path / "custom_short"
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

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--all", "--profile", "code", "-o", str(custom_dir)])
    sys.stdout = old

    files = list(custom_dir.glob("chat-diff-all*"))
    assert len(files) >= 1


# ── _cmd_diff_all empty ───────────────────────────────────────────


def test_cmd_diff_all_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty").mkdir()
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

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--all", "--profile", "code"])
    sys.stdout = old

    assert "No content collected" in out.getvalue()


# ── _cmd_snapshot info full details ───────────────────────────────


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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "info-full"])

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "info", "info-full"])
    sys.stdout = old

    output = out.getvalue()
    assert "Snapshot: info-full" in output
    assert "Created:" in output
    assert "Files:" in output
    assert "Pre-commands:" in output
    assert "Profile:" in output
    assert "max_tokens:" in output
    assert "split_mode:" in output


# ── _cmd_snapshot info profile with pre_commands ──────────────────


def test_cmd_snapshot_info_profile_with_pre_commands(tmp_path, monkeypatch):
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
                        "files": ["README.md"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                        "pre_commands": ["echo hello"],
                    }
                },
            }
        )
    )
    (tmp_path / "README.md").write_text("# Test")

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "info-prof"])

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "info", "info-prof", "--profile"])
    sys.stdout = old

    output = out.getvalue()
    assert "directories:" in output
    assert "patterns:" in output
    assert "files:" in output
    assert "pre_commands:" in output


# ── _cmd_snapshot info stats ──────────────────────────────────────


def test_cmd_snapshot_info_stats(tmp_path, monkeypatch):
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "info-stats"])

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "info", "info-stats", "--stats"])
    sys.stdout = old

    output = out.getvalue()
    assert "Files:" in output
    assert "Pre-commands:" in output
    assert "Command:" in output


# ── _cmd_diff legacy profile error ────────────────────────────────


def test_cmd_diff_legacy_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    from arachna.store import _store_root, write_object

    store_dir = _store_root()
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    test_hash = write_object(b"x")
    old_manifest = {
        "id": "old-legacy",
        "name": "old-legacy",
        "created": "2026-01-01T00:00:00",
        "profile": "code",
        "files": {"a.py": f"sha256:{test_hash}"},
    }
    (snapshots_dir / "old-legacy.json").write_text(json.dumps(old_manifest))

    with pytest.raises(SystemExit):
        _cmd_diff(["arachna", "--diff", "--from", "old-legacy"])


# ── _cmd_snapshot create duplicate ────────────────────────────────


def test_cmd_snapshot_create_duplicate(tmp_path, monkeypatch):
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "dup-name"])

    with pytest.raises(SystemExit):
        _cmd_snapshot(
            ["arachna", "--snapshot", "create", "--profile", "code", "--name", "dup-name"]
        )


# ── _cmd_diff --output-dir flag ───────────────────────────────────


def test_cmd_diff_output_dir_long(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original")
    custom_dir = tmp_path / "custom_od"
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "od-cov"])
    (tmp_path / "src" / "main.py").write_text("modified")

    _cmd_diff(
        [
            "arachna",
            "--diff",
            "--from",
            "od-cov",
            "--profile",
            "code",
            "--output-dir",
            str(custom_dir),
        ]
    )

    files = list(custom_dir.glob("chat-diff*"))
    assert len(files) >= 1


# ── _cmd_snapshot update with profile ─────────────────────────────


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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "upd-cov"])

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "update", "upd-cov", "--profile", "code"])
    sys.stdout = old

    assert "updated" in out.getvalue()


# ── _cmd_snapshot update --profile without value ──────────────────


def test_cmd_snapshot_update_profile_missing_value(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "update", "some-id", "--profile"])


# ── _cmd_snapshot create --profile without value ──────────────────


def test_cmd_snapshot_create_profile_missing_value(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "--name", "test"])


# ── _cmd_diff --stat ──────────────────────────────────────────────


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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "stat-cov"])
    (tmp_path / "src" / "main.py").write_text("modified v2")

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "stat-cov", "--profile", "code", "--stat"])
    sys.stdout = old

    output = out.getvalue()
    assert "Modified:" in output
    assert "Added:" in output
    assert "Deleted:" in output
    assert "Tokens:" in output


# ── _cmd_diff --flat ──────────────────────────────────────────────


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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "flat-cov"])
    (tmp_path / "src" / "main.py").write_text("modified flat")

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "flat-cov", "--profile", "code", "--flat"])
    sys.stdout = old

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
