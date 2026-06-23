import json
from unittest.mock import patch

from arachna.config.setup.init import run_defaults, run_interactive


def test_run_defaults_creates_config(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / ".git").mkdir()

    with patch(
        "arachna.config.setup.init.detect_presets", return_value=["python", "docs", "config", "git"]
    ):
        run_defaults(tmp_path, output_dir="out")

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "python" in data["profiles"]
    assert "git" in data["profiles"]
    assert data["output_dir"] == "out"


def test_run_defaults_empty_project(tmp_path):
    (tmp_path / ".git").mkdir()

    with patch("arachna.config.setup.init.detect_presets", return_value=["git"]):
        run_defaults(tmp_path, output_dir="out")

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "git" in data["profiles"]


def test_run_defaults_creates_output_dir(tmp_path):
    (tmp_path / ".git").mkdir()

    with patch("arachna.config.setup.init.detect_presets", return_value=["git"]):
        run_defaults(tmp_path, output_dir="out")

    assert (tmp_path / "out").is_dir()


def test_run_defaults_detects_godot(tmp_path):
    (tmp_path / "project.godot").write_text("x")
    (tmp_path / ".git").mkdir()

    with patch("arachna.config.setup.init.detect_presets", return_value=["godot", "git"]):
        run_defaults(tmp_path, output_dir="out")

    data = json.loads((tmp_path / ".arachna.json").read_text())
    assert "godot" in data["profiles"]


def test_run_defaults_detects_docker(tmp_path):
    (tmp_path / "Dockerfile").write_text("FROM python")
    (tmp_path / ".git").mkdir()

    with patch("arachna.config.setup.init.detect_presets", return_value=["docker", "git"]):
        run_defaults(tmp_path, output_dir="out")

    data = json.loads((tmp_path / ".arachna.json").read_text())
    assert "docker" in data["profiles"]


def test_run_interactive_basic(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / ".git").mkdir()

    with (
        patch("arachna.config.setup.init.detect_presets", return_value=["python", "docs", "git"]),
        patch("builtins.input", side_effect=["TestProject", "out", "16000", "y", "y", "y", "y"]),
    ):
        run_interactive(tmp_path, output_dir=".")

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert data["project_name"] == "TestProject"
    assert data["output_dir"] == "out"


def test_run_interactive_defaults_on_enter(tmp_path):
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / ".git").mkdir()

    with (
        patch("arachna.config.setup.init.detect_presets", return_value=["docs", "git"]),
        patch("builtins.input", side_effect=["", "", "", "y", "y", "y"]),
    ):
        run_interactive(tmp_path, output_dir=".")

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()


def test_run_interactive_decline_profile(tmp_path):
    (tmp_path / "Dockerfile").write_text("FROM python")
    (tmp_path / ".git").mkdir()

    with (
        patch("arachna.config.setup.init.detect_presets", return_value=["docker", "git"]),
        patch("builtins.input", side_effect=["TestProject", "out", "16000", "n", "y", "y"]),
    ):
        run_interactive(tmp_path, output_dir=".")

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "docker" not in data["profiles"]
    assert "git" in data["profiles"]


def test_run_interactive_existing_config_overwrite(tmp_path):
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "old"}))
    (tmp_path / ".git").mkdir()

    with (
        patch("arachna.config.setup.init.detect_presets", return_value=["git"]),
        patch("builtins.input", side_effect=["y", "NewProject", "out", "16000", "y", "y"]),
    ):
        run_interactive(tmp_path, output_dir=".")

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert data["project_name"] == "NewProject"


def test_run_interactive_existing_config_abort(tmp_path):
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "old"}))

    with (
        patch("arachna.config.setup.init.detect_presets", return_value=["git"]),
        patch("builtins.input", side_effect=["n"]),
    ):
        run_interactive(tmp_path, output_dir=".")

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert data["project_name"] == "old"
