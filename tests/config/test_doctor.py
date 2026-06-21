import json
from argparse import Namespace
from unittest.mock import patch

from arachna.cli.doctor import _cmd_doctor
from arachna.config.doctor import print_doctor, run_doctor
from arachna.config.profile_config import ArachnaConfig, ProfileConfig


def test_valid_config(tmp_path):
    (tmp_path / "src").mkdir()
    config = ArachnaConfig(
        profiles={
            "code": ProfileConfig(directories=["src"], max_tokens=16000, split_mode="by_file"),
        }
    )
    report = run_doctor(project_root=tmp_path, config=config)
    assert report["total_errors"] == 0
    assert "code" in report["profiles"]


def test_invalid_split_mode(tmp_path):
    config = ArachnaConfig(
        profiles={
            "bad": ProfileConfig(directories=["src"], max_tokens=100, split_mode="invalid_mode"),
        }
    )
    report = run_doctor(project_root=tmp_path, config=config)
    assert report["total_errors"] >= 1
    assert any("split_mode" in e for e in report["profiles"]["bad"]["errors"])


def test_missing_directory(tmp_path):
    config = ArachnaConfig(
        profiles={
            "code": ProfileConfig(directories=["nonexistent_dir"], max_tokens=100),
        }
    )
    report = run_doctor(project_root=tmp_path, config=config)
    assert report["total_warnings"] >= 1
    assert any("nonexistent_dir" in w for w in report["profiles"]["code"]["warnings"])


def test_missing_file(tmp_path):
    config = ArachnaConfig(
        profiles={
            "code": ProfileConfig(files=["nonexistent.txt"], max_tokens=100),
        }
    )
    report = run_doctor(project_root=tmp_path, config=config)
    assert report["total_warnings"] >= 1
    assert any("nonexistent.txt" in w for w in report["profiles"]["code"]["warnings"])


def test_no_config(tmp_path):
    report = run_doctor(project_root=tmp_path)
    assert "default" in report["profiles"]


def test_minus_one_max_tokens_unlimited(tmp_path):
    config = ArachnaConfig(
        profiles={
            "ok": ProfileConfig(max_tokens=-1, command="echo hi"),
        }
    )
    report = run_doctor(project_root=tmp_path, config=config)
    assert report["total_errors"] == 0


def test_negative_two_max_tokens(tmp_path):
    config = ArachnaConfig(
        profiles={
            "bad": ProfileConfig(max_tokens=-2, command="echo hi"),
        }
    )
    report = run_doctor(project_root=tmp_path, config=config)
    assert report["total_errors"] >= 1
    assert any("max_tokens" in e for e in report["profiles"]["bad"]["errors"])


def test_by_marker_no_marker(tmp_path):
    config = ArachnaConfig(
        profiles={
            "bad": ProfileConfig(split_mode="by_marker", max_tokens=100, command="echo hi"),
        }
    )
    report = run_doctor(project_root=tmp_path, config=config)
    assert report["total_errors"] >= 1
    assert any("split_marker" in e for e in report["profiles"]["bad"]["errors"])


def test_no_content_source(tmp_path):
    config = ArachnaConfig(
        profiles={
            "bad": ProfileConfig(max_tokens=100),
        }
    )
    report = run_doctor(project_root=tmp_path, config=config)
    assert report["total_errors"] >= 1
    assert any("No content source" in e for e in report["profiles"]["bad"]["errors"])


def test_print_doctor_output():
    report = {
        "profiles": {"test": {"errors": [], "warnings": []}},
        "gitignore": [],
        "total_errors": 0,
        "total_warnings": 0,
    }
    print_doctor(report)


def test_print_doctor_with_errors():
    report = {
        "profiles": {
            "bad": {
                "errors": ["max_tokens: must be >= -1, got -2"],
                "warnings": ["file not found: x.txt"],
            }
        },
        "gitignore": ["Loaded 5 gitignore patterns"],
        "total_errors": 1,
        "total_warnings": 1,
    }
    print_doctor(report)


def test_cmd_doctor_valid(tmp_path):
    (tmp_path / "src").mkdir()
    config_dict = {
        "project_name": "test",
        "output_dir": "out",
        "_root": str(tmp_path),
        "profiles": {
            "code": ProfileConfig(directories=["src"], max_tokens=16000, split_mode="by_file"),
        },
    }
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
        _cmd_doctor(Namespace(), config_dict)
        mock_exit.assert_called_with(0)


def test_cmd_doctor_invalid(tmp_path):
    config_dict = {
        "project_name": "test",
        "output_dir": "out",
        "_root": str(tmp_path),
        "profiles": {
            "bad": ProfileConfig(max_tokens=-2, command="echo hi"),
        },
    }
    with patch("sys.exit") as mock_exit:
        _cmd_doctor(Namespace(), config_dict)
        mock_exit.assert_called_with(1)
