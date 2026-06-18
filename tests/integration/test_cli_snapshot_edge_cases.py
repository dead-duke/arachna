"""Integration tests for snapshot CLI edge cases — uncovered branches."""

import json

from tests.integration.conftest import _arachna


def test_snapshot_unknown_subcommand(tmp_path):
    """arachna snapshot unknown_cmd exits non-zero (argparse error)."""
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("snapshot", "unknown_cmd", cwd=tmp_path)
    assert result.returncode != 0


def test_snapshot_info_not_found(tmp_path):
    """arachna snapshot info <nonexistent> exits 1."""
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("snapshot", "info", "nonexistent", cwd=tmp_path)
    assert result.returncode == 1
    assert "not found" in result.stdout


def test_snapshot_delete_not_found(tmp_path):
    """arachna snapshot delete <nonexistent> exits 1."""
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("snapshot", "delete", "nonexistent", cwd=tmp_path)
    assert result.returncode == 1
    assert "Error" in result.stdout


def test_snapshot_rename_not_found(tmp_path):
    """arachna snapshot rename <nonexistent> <new> exits 1."""
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("snapshot", "rename", "nonexistent", "newname", cwd=tmp_path)
    assert result.returncode == 1


def test_snapshot_info_legacy_profile(tmp_path):
    """arachna snapshot info on legacy-format snapshot prints legacy marker."""
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    from arachna.snapshot.store import _store_root, write_object

    store_dir = _store_root(tmp_path)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    test_hash = write_object(b"legacy content", root=tmp_path)
    old_manifest = {
        "id": "old-legacy",
        "name": "old-legacy",
        "created": "2026-01-01T00:00:00",
        "profile": "code",
        "files": {"a.py": f"sha256:{test_hash}"},
    }
    (snapshots_dir / "old-legacy.json").write_text(json.dumps(old_manifest))

    result = _arachna("snapshot", "info", "old-legacy", cwd=tmp_path)
    assert result.returncode == 0
    assert "legacy format" in result.stdout


def test_snapshot_info_stats_only(tmp_path):
    """arachna snapshot info --stats shows file counts."""
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "stats-cov", cwd=tmp_path)
    result = _arachna("snapshot", "info", "stats-cov", "--stats", cwd=tmp_path)
    assert result.returncode == 0
    assert "Files:" in result.stdout
    assert "Pre-commands:" in result.stdout


def test_diff_multiple_snapshots_no_from(tmp_path):
    """arachna diff with multiple snapshots and no --from exits 1 with hint."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x")
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "snap-a", cwd=tmp_path)
    _arachna("snapshot", "create", "--profile", "code", "--name", "snap-b", cwd=tmp_path)
    result = _arachna("diff", cwd=tmp_path)
    assert result.returncode == 1
    assert "Multiple snapshots" in result.stdout
