"""Tests for v1.6.4 Watch CLI handlers — now in cli_watch.py."""

import json

import pytest

from arachna.cli_watch import _cmd_diff, _cmd_snapshot


def test_cmd_snapshot_update(tmp_path, monkeypatch):
    """_cmd_snapshot update re-scans and updates a snapshot."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "upd-test"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "update", "upd-test"])
    sys.stdout = old

    assert "updated" in out.getvalue()


def test_cmd_snapshot_update_not_found(tmp_path, monkeypatch):
    """_cmd_snapshot update for non-existent snapshot exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "update", "nonexistent"])


def test_cmd_snapshot_update_no_id(tmp_path, monkeypatch):
    """_cmd_snapshot update without id exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "update"])


def test_cmd_snapshot_update_invalid_id(tmp_path, monkeypatch):
    """_cmd_snapshot update with flag as id exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "update", "--profile"])


def test_cmd_diff_compress_flag(tmp_path, monkeypatch):
    """_cmd_diff with --compress applies compress to profile."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "cmpr-test"])
    (tmp_path / "src" / "main.py").write_text("a\n\n\n\nb\n")

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "cmpr-test", "--profile", "code", "--compress"])
    sys.stdout = old

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "\n\n\n\n" not in content


def test_cmd_diff_with_output_dir_short_flag(tmp_path, monkeypatch):
    """_cmd_diff with -o flag writes to custom directory."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "od-test"])
    (tmp_path / "src" / "main.py").write_text("modified for -o test")

    custom_dir = tmp_path / "custom_diff"
    _cmd_diff(
        ["arachna", "--diff", "--from", "od-test", "--profile", "code", "-o", str(custom_dir)]
    )

    files = list(custom_dir.glob("chat-diff*"))
    assert len(files) >= 1

    default_files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(default_files) == 0


def test_cmd_diff_output_dir_long_flag(tmp_path, monkeypatch):
    """_cmd_diff with --output-dir flag writes to custom directory."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "odl-test"])
    (tmp_path / "src" / "main.py").write_text("modified for --output-dir test")

    custom_dir = tmp_path / "custom_long"
    _cmd_diff(
        [
            "arachna",
            "--diff",
            "--from",
            "odl-test",
            "--profile",
            "code",
            "--output-dir",
            str(custom_dir),
        ]
    )

    files = list(custom_dir.glob("chat-diff*"))
    assert len(files) >= 1


def test_cmd_diff_legacy_profile_error(tmp_path, monkeypatch):
    """_cmd_diff with legacy string profile in manifest exits 1."""
    import json

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
