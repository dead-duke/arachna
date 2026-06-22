from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.gatherer_files import _collect_file_sections, _get_profile_files
from arachna.domain.tokenization.tokenizer import count_tokens


def _profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=[],
        patterns=[],
        use_gitignore=False,
        files=[],
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_collect_file_sections_resolves_relative_to_root(tmp_path):
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog")
    p = _profile(files=["README.md", "CHANGELOG.md"])
    sections = _collect_file_sections(p, [], count_tokens, root=tmp_path, verbose=False)
    assert len(sections) == 2
    paths = [s[0] for s in sections]
    assert str(tmp_path / "README.md") in paths
    assert str(tmp_path / "CHANGELOG.md") in paths


def test_collect_file_sections_skips_missing_relative_to_root(tmp_path):
    p = _profile(files=["nonexistent.md"])
    sections = _collect_file_sections(p, [], count_tokens, root=tmp_path, verbose=False)
    assert len(sections) == 0


def test_get_profile_files_resolves_relative_to_root(tmp_path):
    (tmp_path / "config.ini").write_text("key=value")
    p = _profile(files=["config.ini"])
    files = _get_profile_files(p, [], root=tmp_path)
    assert len(files) == 1
    assert files[0] == tmp_path / "config.ini"


def test_get_profile_files_skips_missing_relative_to_root(tmp_path):
    p = _profile(files=["ghost.txt"])
    files = _get_profile_files(p, [], root=tmp_path)
    assert len(files) == 0
