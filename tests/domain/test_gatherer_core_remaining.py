"""Tests for remaining uncovered paths in gatherer_core.py."""

from unittest.mock import patch

from arachna.domain.gatherer_core import (
    _collect_file_sections,
    _collect_pre_commands,
    _get_profile_files,
)
from arachna.domain.tokenizer import count_tokens


def test_pre_command_long_label_is_truncated(tmp_path):
    """Pre_command label longer than 50 chars gets truncated with ellipsis."""
    long_cmd = "echo " + "x" * 60
    with patch("arachna.domain.gatherer_core.run_pre_commands") as mock_run:
        mock_run.return_value = [(long_cmd, "output")]
        result = _collect_pre_commands({"pre_commands": [long_cmd]}, count_tokens, root=tmp_path)
    assert len(result) == 1
    assert result[0][0].endswith("...")


def test_collect_file_sections_skips_missing_file(tmp_path):
    """_collect_file_sections skips files that don't exist on disk."""
    profile = {"files": ["nonexistent.py"], "use_gitignore": False}
    sections = _collect_file_sections(profile, [], count_tokens, root=tmp_path, verbose=False)
    assert len(sections) == 0


def test_get_profile_files_skips_directories(tmp_path):
    """_get_profile_files skips paths that are directories, not files."""
    (tmp_path / "subdir").mkdir()
    profile = {"files": [str(tmp_path / "subdir")]}
    files = _get_profile_files(profile, [])
    assert len(files) == 0


def test_get_profile_files_skips_excluded(tmp_path):
    """_get_profile_files skips files matching exclude patterns."""
    f = tmp_path / "debug.log"
    f.write_text("log")
    profile = {"files": [str(f)]}
    files = _get_profile_files(profile, ["*.log"])
    assert len(files) == 0
