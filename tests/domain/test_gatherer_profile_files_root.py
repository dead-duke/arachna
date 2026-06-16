"""BUG-001 regression: profile files resolved relative to project root."""

from arachna.domain.gatherer_core import _collect_file_sections, _get_profile_files
from arachna.domain.tokenizer import count_tokens


def test_collect_file_sections_resolves_relative_to_root(tmp_path):
    """profile.files paths resolved relative to root, not cwd."""
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog")

    profile = {
        "files": ["README.md", "CHANGELOG.md"],
        "use_gitignore": False,
    }

    sections = _collect_file_sections(profile, [], count_tokens, root=tmp_path, verbose=False)
    assert len(sections) == 2
    paths = [s[0] for s in sections]
    assert str(tmp_path / "README.md") in paths
    assert str(tmp_path / "CHANGELOG.md") in paths


def test_collect_file_sections_skips_missing_relative_to_root(tmp_path):
    """Missing files relative to root are skipped."""
    profile = {
        "files": ["nonexistent.md"],
        "use_gitignore": False,
    }

    sections = _collect_file_sections(profile, [], count_tokens, root=tmp_path, verbose=False)
    assert len(sections) == 0


def test_get_profile_files_resolves_relative_to_root(tmp_path):
    """_get_profile_files resolves paths relative to root."""
    (tmp_path / "config.ini").write_text("key=value")

    profile = {"files": ["config.ini"]}
    files = _get_profile_files(profile, [], root=tmp_path)
    assert len(files) == 1
    assert files[0] == tmp_path / "config.ini"


def test_get_profile_files_skips_missing_relative_to_root(tmp_path):
    """_get_profile_files skips files not found relative to root."""
    profile = {"files": ["ghost.txt"]}
    files = _get_profile_files(profile, [], root=tmp_path)
    assert len(files) == 0
