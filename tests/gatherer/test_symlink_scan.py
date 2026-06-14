"""Coverage for _scan_directories symlink handling."""

from arachna.gatherer import _scan_directories


def test_scan_skips_symlink_directory(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "main.py").write_text("code")

    link_dir = tmp_path / "link"
    link_dir.symlink_to(real_dir)

    result = _scan_directories(
        {"directories": [str(link_dir)], "patterns": ["*.py"]},
        exclude=[],
        root=tmp_path,
    )
    assert len(result) == 0


def test_scan_skips_symlink_file(tmp_path):
    real_dir = tmp_path / "src"
    real_dir.mkdir()
    real_file = real_dir / "real.py"
    real_file.write_text("code")

    link_file = real_dir / "link.py"
    link_file.symlink_to(real_file)

    result = _scan_directories(
        {"directories": [str(real_dir)], "patterns": ["*.py"]},
        exclude=[],
        root=tmp_path,
    )
    paths = [str(p) for p in result]
    assert str(real_file) in paths
    assert str(link_file) not in paths


def test_scan_pattern_with_dot_dot(tmp_path):
    real_dir = tmp_path / "src"
    real_dir.mkdir()
    (real_dir / "main.py").write_text("code")

    result = _scan_directories(
        {"directories": [str(real_dir)], "patterns": ["../*.py"]},
        exclude=[],
        root=tmp_path,
    )
    assert len(result) == 0
