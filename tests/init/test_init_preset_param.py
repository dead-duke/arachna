import json
from unittest.mock import patch

from arachna.init import run_defaults, run_interactive


def test_run_defaults_preset_filters_detection(tmp_path, monkeypatch):
    """run_defaults with preset='godot' only creates godot profile."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "project.godot").write_text("x")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    (tmp_path / ".git").mkdir()

    run_defaults(output_dir="out", preset="godot")

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "godot" in data["profiles"]
    # Python should NOT be detected when preset is explicit
    assert "python" not in data["profiles"]


def test_run_defaults_preset_unknown(tmp_path, monkeypatch):
    """run_defaults with unknown preset creates empty config."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()

    run_defaults(output_dir="out", preset="nonexistent_preset")

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert data["profiles"] == {}


def test_run_interactive_with_preset_param(tmp_path, monkeypatch):
    """run_interactive receives preset parameter and passes it to detect_presets."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "project.godot").write_text("x")
    (tmp_path / ".git").mkdir()

    with (
        patch("arachna.init.detect_presets") as mock_detect,
        patch(
            "builtins.input",
            side_effect=[
                "TestProject",
                "out",
                "16000",
                "y",
                "y",
            ],
        ),
    ):
        mock_detect.return_value = ["godot"]
        run_interactive(output_dir=".", preset="godot")

    # Verify detect_presets was called with preset_name="godot"
    mock_detect.assert_called_once_with(preset_name="godot")


def test_run_interactive_preset_param_passed_to_detect(tmp_path, monkeypatch):
    """run_interactive passes preset to detect_presets, not ignoring it."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()

    with (
        patch("arachna.init.detect_presets") as mock_detect,
        patch(
            "builtins.input",
            side_effect=[
                "Test",
                "out",
                "16000",
                "y",
                "y",
            ],
        ),
    ):
        mock_detect.return_value = ["git"]
        run_interactive(output_dir=".", preset="docker")

    mock_detect.assert_called_once_with(preset_name="docker")
