"""Tests for remote repository collection — v4.1.0."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from arachna.domain.remote import collect_remote


def test_collect_remote_blocks_non_http_urls(tmp_path):
    """ftp:// and file:// URLs are rejected before any git call."""
    with pytest.raises(ValueError, match="Only http:// and https://"):
        collect_remote("ftp://evil.com/repo.git", root=tmp_path)

    with pytest.raises(ValueError, match="Only http:// and https://"):
        collect_remote("file:///etc/passwd", root=tmp_path)


def test_collect_remote_allows_http_and_https(tmp_path):
    """http:// and https:// pass URL validation."""
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(RuntimeError, match="git is not installed"),
    ):
        collect_remote("http://example.com/repo.git", root=tmp_path)

    with (
        patch("shutil.which", return_value=None),
        pytest.raises(RuntimeError, match="git is not installed"),
    ):
        collect_remote("https://github.com/user/repo.git", root=tmp_path)


def test_collect_remote_git_not_found(tmp_path):
    """Clear error when git is not on PATH."""
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(RuntimeError, match="git is not installed"),
    ):
        collect_remote("https://github.com/user/repo.git", root=tmp_path)


def test_collect_remote_clone_failure(tmp_path):
    """Git clone error propagates as CalledProcessError."""
    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git clone")
        with pytest.raises(subprocess.CalledProcessError):
            collect_remote("https://github.com/user/repo.git", root=tmp_path)


def test_collect_remote_success(tmp_path):
    """Happy path: clone succeeds, auto-detected preset used, summary returned."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    mock_result = MagicMock()
    mock_result.files = ["chat-code_1.md"]
    mock_result.parts = ["content"]
    mock_result.tokens = 100
    mock_result.metrics = MagicMock()
    mock_result.metrics.files_read = 1
    mock_result.metrics.extract_time_ms = 5.0

    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run") as mock_run,
        patch("arachna.domain.remote.collect", return_value=mock_result),
        patch("arachna.domain.remote.detect_presets", return_value=["python"]),
        patch("tempfile.mkdtemp", return_value=str(tmp_path / "tmpdir")),
    ):
        mock_run.return_value = MagicMock()
        result = collect_remote("https://github.com/user/repo.git", root=tmp_path)

    assert "Repository: https://github.com/user/repo.git" in result
    assert "Profile: python" in result
    assert "Files collected: 1" in result
    assert "Tokens: 100" in result


def test_collect_remote_no_presets_falls_back_to_full(tmp_path):
    """When no presets detected, 'full' profile is used as fallback."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    mock_result = MagicMock()
    mock_result.files = ["chat-full_1.md"]
    mock_result.parts = ["content"]
    mock_result.tokens = 50
    mock_result.metrics = None

    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run") as mock_run,
        patch("arachna.domain.remote.collect", return_value=mock_result),
        patch("arachna.domain.remote.detect_presets", return_value=[]),
        patch("tempfile.mkdtemp", return_value=str(tmp_path / "tmpdir")),
    ):
        mock_run.return_value = MagicMock()
        result = collect_remote("https://github.com/user/repo.git", root=tmp_path)

    assert "Profile: full" in result


def test_collect_remote_cleans_up_temp_dir(tmp_path):
    """Temp directory is removed after successful collection."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    tmpdir_path = tmp_path / "tmpdir"
    tmpdir_path.mkdir()

    mock_result = MagicMock()
    mock_result.files = []
    mock_result.parts = []
    mock_result.tokens = 0
    mock_result.metrics = None

    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run") as mock_run,
        patch("arachna.domain.remote.collect", return_value=mock_result),
        patch("arachna.domain.remote.detect_presets", return_value=[]),
        patch("tempfile.mkdtemp", return_value=str(tmpdir_path)),
    ):
        mock_run.return_value = MagicMock()
        collect_remote("https://github.com/user/repo.git", root=tmp_path)

    assert not tmpdir_path.exists()


def test_collect_remote_cleanup_on_error(tmp_path):
    """Temp directory is removed even when git clone fails."""
    tmpdir_path = tmp_path / "tmpdir"
    tmpdir_path.mkdir()

    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git clone")),
        patch("tempfile.mkdtemp", return_value=str(tmpdir_path)),
        pytest.raises(subprocess.CalledProcessError),
    ):
        collect_remote("https://github.com/user/repo.git", root=tmp_path)

    assert not tmpdir_path.exists()


def test_collect_remote_existing_config_profile(tmp_path):
    """When cloned repo has .arachna.json with the requested profile, use it directly."""
    mock_result = MagicMock()
    mock_result.files = ["chat-api_1.md"]
    mock_result.parts = ["content"]
    mock_result.tokens = 200
    mock_result.metrics = None

    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run") as mock_run,
        patch("arachna.domain.remote.collect", return_value=mock_result),
        patch("arachna.domain.remote.load_config") as mock_load_config,
        patch("tempfile.mkdtemp", return_value=str(tmp_path / "tmpdir")),
    ):
        mock_run.return_value = MagicMock()
        mock_load_config.return_value = {
            "profiles": {"go": {"directories": ["."], "max_tokens": 16000}}
        }
        result = collect_remote("https://github.com/user/repo.git", profile="go", root=tmp_path)

    assert "Profile: go" in result


def test_collect_remote_profile_not_in_config_falls_back(tmp_path):
    """When requested profile is not in cloned config, fall back to auto-detection."""
    mock_result = MagicMock()
    mock_result.files = ["chat-python_1.md"]
    mock_result.parts = ["content"]
    mock_result.tokens = 300
    mock_result.metrics = None

    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run") as mock_run,
        patch("arachna.domain.remote.collect", return_value=mock_result),
        patch("arachna.domain.remote.load_config") as mock_load_config,
        patch("arachna.domain.remote.detect_presets", return_value=["python", "docs"]),
        patch("tempfile.mkdtemp", return_value=str(tmp_path / "tmpdir")),
    ):
        mock_run.return_value = MagicMock()
        mock_load_config.return_value = {
            "profiles": {"go": {"directories": ["."], "max_tokens": 16000}}
        }
        result = collect_remote("https://github.com/user/repo.git", profile="rust", root=tmp_path)

    assert "Profile: python" in result
