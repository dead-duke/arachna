import json
from unittest.mock import patch

from arachna.config.setup.init import run_defaults, run_interactive


def test_run_defaults_preset_filters_detection(tmp_path):
    (tmp_path / "project.godot").write_text("x")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    (tmp_path / ".git").mkdir()

    run_defaults(output_dir="out", preset="godot", root=tmp_path)

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "godot" in data["profiles"]
    assert "python" not in data["profiles"]


def test_run_defaults_preset_unknown(tmp_path):
    (tmp_path / ".git").mkdir()

    run_defaults(output_dir="out", preset="nonexistent_preset", root=tmp_path)

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert data["profiles"] == {}


def test_run_interactive_with_preset_param(tmp_path):
    (tmp_path / "project.godot").write_text("x")
    (tmp_path / ".git").mkdir()

    with (
        patch("arachna.config.setup.init.detect_presets") as mock_detect,
        patch("builtins.input", side_effect=["TestProject", "out", "16000", "y", "y"]),
    ):
        mock_detect.return_value = ["godot"]
        run_interactive(output_dir=".", preset="godot", root=tmp_path)

    mock_detect.assert_called_once_with(preset_name="godot", root=tmp_path)


def test_run_interactive_preset_filters_autodetection(tmp_path):
    (tmp_path / "project.godot").write_text("x")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / ".git").mkdir()

    with patch("builtins.input", side_effect=["TestProject", "out", "16000", "y", "y"]):
        run_interactive(output_dir=".", preset="godot", root=tmp_path)

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "godot" in data["profiles"]
    assert "python" not in data["profiles"]
    assert "docs" not in data["profiles"]
    assert len(data["profiles"]) == 1


def test_run_interactive_no_preset_full_autodetect(tmp_path):
    (tmp_path / "project.godot").write_text("x")
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / ".git").mkdir()

    with patch("builtins.input", side_effect=["TestProject", "out", "16000", "y", "y", "y", "y"]):
        run_interactive(output_dir=".", root=tmp_path)

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "godot" in data["profiles"]
    assert "docs" in data["profiles"]
    assert "git" in data["profiles"]
