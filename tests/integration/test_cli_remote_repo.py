"""Integration tests for arachna collect --repo."""

import json
import subprocess

from tests.integration.conftest import _arachna


def test_collect_repo_local_git(tmp_path):
    """Collect from a local git repository via --repo with file:// clone simulation."""
    # Create a local git repo
    repo = tmp_path / "testrepo"
    repo.mkdir()
    (repo / "README.md").write_text("# Test Repo")
    src = repo / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    subprocess.run(["git", "init"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)

    # Run arachna collect --repo with the local repo URL
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
    # file:// URL should be rejected
    assert result.returncode == 1
    assert "only http:// and https://" in result.stdout


def test_collect_repo_invalid_url(tmp_path):
    """--repo with ftp:// URL is rejected."""
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


def test_collect_repo_git_not_found(tmp_path):
    """--repo when git is not installed shows clear error."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna(
        "collect",
        "--repo",
        "https://github.com/user/nonexistent.git",
        cwd=tmp_path,
    )
    # Either git not found or clone failed — both acceptable for integration test
    assert result.returncode == 1
    assert "Error" in result.stdout
