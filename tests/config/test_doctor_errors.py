"""Tests for error handling branches in doctor.py."""

from unittest.mock import patch

from arachna.config.doctor import run_doctor


def test_doctor_project_root_not_dir(tmp_path):
    report = run_doctor(project_root=tmp_path / "nonexistent")
    assert "gitignore" in report
    assert any("not a directory" in msg for msg in report["gitignore"])


def test_doctor_gitignore_os_error(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".arachna.json").write_text(
        '{"profiles": {"code": {"directories": ["src"], "max_tokens": 16000, "split_mode": "by_file"}}}'
    )

    def failing_load_gitignore_patterns(root):
        raise OSError("Disk error")

    with patch("arachna.config.doctor.load_gitignore_patterns", failing_load_gitignore_patterns):
        report = run_doctor(project_root=tmp_path)
    assert "gitignore" in report
    assert any("Error loading .gitignore" in msg for msg in report["gitignore"])
    assert report["total_warnings"] >= 1
