"""Tests for remote repository collection — v4.1.1."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from arachna.config.profile_config import ProfileConfig
from arachna.config.remote import _select_profile, collect_remote

# -- URL validation -----------------------------------------------------


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

    mock_metrics = MagicMock()
    mock_metrics.files_read = 1
    mock_metrics.extract_time_ms = 5.0

    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run") as mock_run,
        patch(
            "arachna.config.remote._domain_collect",
            return_value=(
                ["chat-code_1.md"],
                {"chat-code_1.md": 100},
                ["content"],
                mock_metrics,
            ),
        ),
        patch("arachna.config.remote.detect_presets", return_value=["python"]),
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

    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run") as mock_run,
        patch(
            "arachna.config.remote._domain_collect",
            return_value=(
                ["chat-full_1.md"],
                {"chat-full_1.md": 50},
                ["content"],
                None,
            ),
        ),
        patch("arachna.config.remote.detect_presets", return_value=[]),
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

    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run") as mock_run,
        patch(
            "arachna.config.remote._domain_collect",
            return_value=(
                [],
                {},
                [],
                None,
            ),
        ),
        patch("arachna.config.remote.detect_presets", return_value=[]),
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


# -- Profile selection — explicit --profile ----------------------------------


def test_select_profile_exact_match():
    """--profile go, config has go -> uses it."""
    result = _select_profile(
        requested="go",
        profiles={"go": ProfileConfig(), "python": ProfileConfig()},
        has_config=True,
        repo_path=Path("/tmp/repo"),
    )
    assert result == "go"


def test_select_profile_not_found_with_config():
    """--profile rust, config has go/python -> ValueError with names."""
    with pytest.raises(ValueError, match="Profile 'rust' not found.*go, python"):
        _select_profile(
            requested="rust",
            profiles={"go": ProfileConfig(), "python": ProfileConfig()},
            has_config=True,
            repo_path=Path("/tmp/repo"),
        )


def test_select_profile_not_found_no_config():
    """--profile python, no .arachna.json -> ValueError."""
    with pytest.raises(ValueError, match="no .arachna.json"):
        _select_profile(
            requested="python",
            profiles={},
            has_config=False,
            repo_path=Path("/tmp/repo"),
        )


# -- Profile selection — auto (requested="full") -----------------------------


def test_select_auto_one_remote():
    """One remote:true profile -> uses it."""
    result = _select_profile(
        requested="full",
        profiles={
            "go": ProfileConfig(remote=True),
            "python": ProfileConfig(),
        },
        has_config=True,
        repo_path=Path("/tmp/repo"),
    )
    assert result == "go"


def test_select_auto_multiple_remote():
    """Multiple remote:true -> ValueError with names."""
    with pytest.raises(ValueError, match="Multiple profiles with remote:true.*go, python"):
        _select_profile(
            requested="full",
            profiles={
                "go": ProfileConfig(remote=True),
                "python": ProfileConfig(remote=True),
            },
            has_config=True,
            repo_path=Path("/tmp/repo"),
        )


def test_select_auto_no_remote_autodetect():
    """No remote:true, has .arachna.json -> auto-detect via presets."""
    with patch("arachna.config.remote.detect_presets", return_value=["python", "docs"]):
        result = _select_profile(
            requested="full",
            profiles={"go": ProfileConfig()},
            has_config=True,
            repo_path=Path("/tmp/repo"),
        )
    assert result == "python"


def test_select_auto_no_remote_no_presets():
    """No remote:true, no presets detected -> 'full'."""
    with patch("arachna.config.remote.detect_presets", return_value=[]):
        result = _select_profile(
            requested="full",
            profiles={},
            has_config=True,
            repo_path=Path("/tmp/repo"),
        )
    assert result == "full"


def test_select_auto_no_config_autodetect():
    """No .arachna.json -> auto-detect via presets."""
    with patch("arachna.config.remote.detect_presets", return_value=["rust"]):
        result = _select_profile(
            requested="full",
            profiles={},
            has_config=False,
            repo_path=Path("/tmp/repo"),
        )
    assert result == "rust"


def test_select_auto_no_config_no_presets():
    """No .arachna.json, no presets -> 'full'."""
    with patch("arachna.config.remote.detect_presets", return_value=[]):
        result = _select_profile(
            requested="full",
            profiles={},
            has_config=False,
            repo_path=Path("/tmp/repo"),
        )
    assert result == "full"


# -- collect_remote with --profile flag --------------------------------------


def test_collect_remote_exact_profile(tmp_path):
    """--profile go with matching config uses go."""
    repo_path = tmp_path / "tmpdir" / "repo"
    repo_path.mkdir(parents=True)
    (repo_path / ".arachna.json").write_text(
        '{"profiles": {"go": {"directories": ["."], "max_tokens": 16000}}}'
    )

    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run") as mock_run,
        patch(
            "arachna.config.remote._domain_collect",
            return_value=(
                ["chat-go_1.md"],
                {"chat-go_1.md": 200},
                ["content"],
                None,
            ),
        ),
        patch("tempfile.mkdtemp", return_value=str(tmp_path / "tmpdir")),
    ):
        mock_run.return_value = MagicMock()
        result = collect_remote("https://github.com/user/repo.git", profile="go", root=tmp_path)

    assert "Profile: go" in result


def test_collect_remote_profile_not_in_config_raises(tmp_path):
    """--profile rust, not in config -> ValueError."""
    repo_path = tmp_path / "tmpdir" / "repo"
    repo_path.mkdir(parents=True)
    (repo_path / ".arachna.json").write_text(
        '{"profiles": {"go": {"directories": ["."], "max_tokens": 16000}}}'
    )

    with (
        patch("shutil.which", return_value="/usr/bin/git"),
        patch("subprocess.run") as mock_run,
        patch("tempfile.mkdtemp", return_value=str(tmp_path / "tmpdir")),
        pytest.raises(ValueError, match="Profile 'rust' not found"),
    ):
        mock_run.return_value = MagicMock()
        collect_remote("https://github.com/user/repo.git", profile="rust", root=tmp_path)
