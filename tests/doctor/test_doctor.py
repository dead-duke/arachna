import json
from argparse import Namespace
from unittest.mock import patch

from arachna.__main__ import _cmd_doctor, _cmd_install_hook
from arachna.doctor import print_doctor, run_doctor


def test_valid_config(tmp_path, monkeypatch):
    """Doctor reports no errors for a valid config."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "code": {"directories": ["src"], "max_tokens": 16000, "split_mode": "by_file"}
                }
            }
        )
    )
    report = run_doctor()
    assert report["total_errors"] == 0
    assert "code" in report["profiles"]


def test_invalid_split_mode(tmp_path, monkeypatch):
    """Doctor reports error for invalid split_mode."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "bad": {
                        "directories": ["src"],
                        "max_tokens": 100,
                        "split_mode": "invalid_mode",
                    }
                }
            }
        )
    )
    report = run_doctor()
    assert report["total_errors"] >= 1
    assert any("split_mode" in e for e in report["profiles"]["bad"]["errors"])


def test_missing_directory(tmp_path, monkeypatch):
    """Doctor warns about non-existent directories."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "code": {
                        "directories": ["nonexistent_dir"],
                        "max_tokens": 100,
                    }
                }
            }
        )
    )
    report = run_doctor()
    assert report["total_warnings"] >= 1
    assert any("nonexistent_dir" in w for w in report["profiles"]["code"]["warnings"])


def test_missing_file(tmp_path, monkeypatch):
    """Doctor warns about non-existent files."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "code": {
                        "files": ["nonexistent.txt"],
                        "max_tokens": 100,
                    }
                }
            }
        )
    )
    report = run_doctor()
    assert report["total_warnings"] >= 1
    assert any("nonexistent.txt" in w for w in report["profiles"]["code"]["warnings"])


def test_no_config(tmp_path, monkeypatch):
    """Doctor works without .arachna.json (uses default profile)."""
    monkeypatch.chdir(tmp_path)
    report = run_doctor()
    assert "default" in report["profiles"]


def test_zero_max_tokens(tmp_path, monkeypatch):
    """Doctor reports error for zero max_tokens."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"bad": {"max_tokens": 0, "command": "echo hi"}}})
    )
    report = run_doctor()
    assert report["total_errors"] >= 1
    assert any("max_tokens" in e for e in report["profiles"]["bad"]["errors"])


def test_by_marker_no_marker(tmp_path, monkeypatch):
    """Doctor reports error for by_marker without split_marker."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "bad": {
                        "split_mode": "by_marker",
                        "max_tokens": 100,
                        "command": "echo hi",
                    }
                }
            }
        )
    )
    report = run_doctor()
    assert report["total_errors"] >= 1
    assert any("split_marker" in e for e in report["profiles"]["bad"]["errors"])


def test_no_content_source(tmp_path, monkeypatch):
    """Doctor reports error when no content source is specified."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {"bad": {"max_tokens": 100}}}))
    report = run_doctor()
    assert report["total_errors"] >= 1
    assert any("No content source" in e for e in report["profiles"]["bad"]["errors"])


def test_print_doctor_output():
    """print_doctor prints without raising."""
    report = {
        "profiles": {"test": {"errors": [], "warnings": []}},
        "gitignore": [],
        "total_errors": 0,
        "total_warnings": 0,
    }
    print_doctor(report)


def test_print_doctor_with_errors():
    """print_doctor handles errors in output."""
    report = {
        "profiles": {
            "bad": {
                "errors": ["max_tokens: must be > 0, got 0"],
                "warnings": ["file not found: x.txt"],
            }
        },
        "gitignore": ["Loaded 5 gitignore patterns"],
        "total_errors": 1,
        "total_warnings": 1,
    }
    print_doctor(report)


def test_cmd_doctor_valid(tmp_path, monkeypatch):
    """_cmd_doctor exits 0 for valid config."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "code": {"directories": ["src"], "max_tokens": 16000, "split_mode": "by_file"}
                }
            }
        )
    )

    with patch("sys.exit") as mock_exit:
        _cmd_doctor()
        mock_exit.assert_called_with(0)


def test_cmd_doctor_invalid(tmp_path, monkeypatch):
    """_cmd_doctor exits 1 for invalid config."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"bad": {"max_tokens": 0, "command": "echo hi"}}})
    )

    with patch("sys.exit") as mock_exit:
        _cmd_doctor()
        mock_exit.assert_called_with(1)


def test_cmd_install_hook_success(tmp_path, monkeypatch):
    """_cmd_install_hook exits 0 on success."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    with patch("sys.exit") as mock_exit:
        _cmd_install_hook(Namespace(force=False))
        mock_exit.assert_called_with(0)


def test_cmd_install_hook_failure(tmp_path, monkeypatch):
    """_cmd_install_hook exits 1 on failure."""
    monkeypatch.chdir(tmp_path)

    with patch("sys.exit") as mock_exit:
        _cmd_install_hook(Namespace(force=False))
        mock_exit.assert_called_with(1)


def test_cmd_install_hook_existing_refuses(tmp_path, monkeypatch):
    """_cmd_install_hook exits 1 when hook exists and no --force."""
    monkeypatch.chdir(tmp_path)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (git_dir / "hooks" / "post-commit").write_text("#!/bin/sh\necho old")
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    with patch("sys.exit") as mock_exit:
        _cmd_install_hook(Namespace(force=False))
        mock_exit.assert_called_with(1)
