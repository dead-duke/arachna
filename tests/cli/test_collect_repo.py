"""Tests for _cmd_collect_repo — arachna collect --repo <url>."""

import sys
from argparse import Namespace
from io import StringIO
from unittest.mock import patch

import pytest

from arachna.cli.collect import _cmd_collect_repo


def _repo_args(url, profile=None, output_dir=None):
    return Namespace(repo=url, profile=profile, output_dir=output_dir)


def test_repo_invalid_url_ftp(tmp_path, make_config):
    config = make_config(tmp_path)
    with pytest.raises(SystemExit) as exc:
        _cmd_collect_repo(_repo_args("ftp://evil.com/repo.git"), config)
    assert exc.value.code == 1


def test_repo_invalid_url_file(tmp_path, make_config):
    config = make_config(tmp_path)
    with pytest.raises(SystemExit) as exc:
        _cmd_collect_repo(_repo_args("file:///etc/passwd"), config)
    assert exc.value.code == 1


def test_repo_runtime_error(tmp_path, make_config):
    config = make_config(tmp_path)
    with patch("arachna.domain.remote.collect_remote", side_effect=RuntimeError("git not found")):
        with pytest.raises(SystemExit) as exc:
            _cmd_collect_repo(_repo_args("https://github.com/user/repo.git"), config)
        assert exc.value.code == 1


def test_repo_generic_exception(tmp_path, make_config):
    config = make_config(tmp_path)
    with patch("arachna.domain.remote.collect_remote", side_effect=OSError("disk full")):
        with pytest.raises(SystemExit) as exc:
            _cmd_collect_repo(_repo_args("https://github.com/user/repo.git"), config)
        assert exc.value.code == 1


def test_repo_success(tmp_path, make_config):
    config = make_config(tmp_path)
    with patch("arachna.domain.remote.collect_remote", return_value="Collected: 5 files"):
        out = StringIO()
        old = sys.stdout
        sys.stdout = out
        _cmd_collect_repo(_repo_args("https://github.com/user/repo.git"), config)
        sys.stdout = old
        assert "Collected:" in out.getvalue()


def test_repo_with_profile(tmp_path, make_config):
    config = make_config(tmp_path)
    with patch("arachna.domain.remote.collect_remote") as mock:
        mock.return_value = "done"
        _cmd_collect_repo(_repo_args("https://github.com/user/repo.git", profile="python"), config)
        mock.assert_called_once()
        assert mock.call_args[1]["profile"] == "python"


def test_repo_with_output_dir(tmp_path, make_config):
    config = make_config(tmp_path)
    custom = str(tmp_path / "custom")
    with patch("arachna.domain.remote.collect_remote") as mock:
        mock.return_value = "done"
        _cmd_collect_repo(_repo_args("https://github.com/user/repo.git", output_dir=custom), config)
        mock.assert_called_once()
        assert mock.call_args[1]["output_dir"] == custom
