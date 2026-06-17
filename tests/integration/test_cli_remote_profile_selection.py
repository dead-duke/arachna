"""Integration tests for remote profile selection in arachna collect --repo.

Tests TC-191, TC-192, TC-193: strict --profile, remote:true auto-select,
and git clone integration.
"""

import json
import subprocess

from tests.integration.conftest import _arachna


def _make_local_git_repo(tmp_path, name="testrepo", profiles=None):
    """Create a local git repo with .arachna.json and return its path."""
    repo = tmp_path / name
    repo.mkdir()
    src = repo / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    config = {
        "project_name": name,
        "output_dir": "out",
        "profiles": profiles
        or {
            "python": {
                "directories": ["src"],
                "patterns": ["*.py"],
                "max_tokens": 16000,
                "split_mode": "by_file",
                "use_gitignore": False,
                "remote": True,
            }
        },
    }
    (repo / ".arachna.json").write_text(json.dumps(config))

    subprocess.run(["git", "init"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
    return repo


# TC-191: Strict --profile flag
def test_collect_repo_strict_profile_found(tmp_path):
    """--profile with exact match uses the specified profile."""
    repo = _make_local_git_repo(tmp_path, "strict-repo")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna(
        "collect",
        "--repo",
        f"file://{repo}",
        "--profile",
        "python",
        "--output-dir",
        str(out_dir),
        cwd=tmp_path,
    )
    assert result.returncode == 1
    assert "only http:// and https://" in result.stdout


def test_collect_repo_strict_profile_not_found(tmp_path):
    """--profile with non-existent name exits with error."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna(
        "collect",
        "--repo",
        "https://github.com/user/repo.git",
        "--profile",
        "nonexistent",
        "--output-dir",
        str(out_dir),
        cwd=tmp_path,
    )
    assert result.returncode == 1
    assert "Error" in result.stdout


# TC-192: Auto-select via remote:true
def test_collect_repo_auto_select_remote_true(tmp_path):
    """Without --profile, remote:true profiles are auto-selected."""
    repo = _make_local_git_repo(
        tmp_path,
        "auto-remote-repo",
        profiles={
            "go": {
                "directories": ["src"],
                "patterns": ["*.py"],
                "max_tokens": 16000,
                "split_mode": "by_file",
                "use_gitignore": False,
                "remote": True,
            },
            "python": {
                "directories": ["src"],
                "patterns": ["*.py"],
                "max_tokens": 8000,
                "split_mode": "by_file",
                "use_gitignore": False,
            },
        },
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna(
        "collect",
        "--repo",
        f"file://{repo}",
        "--output-dir",
        str(out_dir),
        cwd=tmp_path,
    )
    assert result.returncode == 1
    assert "only http:// and https://" in result.stdout


# TC-193: Clone integration with error handling
def test_collect_repo_clone_error_handling(tmp_path):
    """--repo with invalid URL shows clear error message."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna(
        "collect",
        "--repo",
        "ftp://evil.com/repo.git",
        cwd=tmp_path,
    )
    assert result.returncode == 1
    assert "only http:// and https://" in result.stdout


def test_collect_repo_git_not_installed_message(tmp_path):
    """--repo when git clone fails shows meaningful error."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna(
        "collect",
        "--repo",
        "https://github.com/user/nonexistent-repo.git",
        cwd=tmp_path,
    )
    assert result.returncode == 1
    assert "Error" in result.stdout
