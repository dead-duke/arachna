from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.gatherer import _scan_directories


def test_scan_skips_symlink_directory(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "main.py").write_text("code")

    link_dir = tmp_path / "link"
    link_dir.symlink_to(real_dir)

    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=[str(link_dir)],
        patterns=["*.py"],
        use_gitignore=False,
    )
    result = _scan_directories(p, exclude=[], root=tmp_path)
    assert len(result) == 0


def test_scan_skips_symlink_file(tmp_path):
    real_dir = tmp_path / "src"
    real_dir.mkdir()
    real_file = real_dir / "real.py"
    real_file.write_text("code")

    link_file = real_dir / "link.py"
    link_file.symlink_to(real_file)

    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=[str(real_dir)],
        patterns=["*.py"],
        use_gitignore=False,
    )
    result = _scan_directories(p, exclude=[], root=tmp_path)
    paths = [str(path) for path in result]
    assert str(real_file) in paths
    assert str(link_file) not in paths


def test_scan_pattern_with_dot_dot(tmp_path):
    real_dir = tmp_path / "src"
    real_dir.mkdir()
    (real_dir / "main.py").write_text("code")

    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=[str(real_dir)],
        patterns=["../*.py"],
        use_gitignore=False,
    )
    result = _scan_directories(p, exclude=[], root=tmp_path)
    assert len(result) == 0
