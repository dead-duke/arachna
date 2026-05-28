import json
from unittest.mock import patch

from arachna.init import run_defaults, run_interactive


def test_run_defaults_creates_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    (tmp_path / "README.md").write_text("# Project")
    run_defaults(output_dir="out")
    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "code" in data["profiles"]
    assert "git" in data["profiles"]
    assert data["output_dir"] == "out"


def test_run_defaults_empty_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_defaults(output_dir="out")
    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "git" in data["profiles"]
    assert "code" not in data["profiles"]


def test_run_defaults_creates_output_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_defaults(output_dir="out")
    assert (tmp_path / "out").is_dir()


def test_run_defaults_detects_tests(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_main.py").write_text("def test(): pass")
    run_defaults(output_dir="out")
    data = json.loads((tmp_path / ".arachna.json").read_text())
    assert "tests" in data["profiles"]


def test_run_interactive_basic(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    (tmp_path / "README.md").write_text("# Project")
    with patch(
        "builtins.input",
        side_effect=[
            "TestProject",  # project name
            "out",  # output dir
            "16000",  # max tokens
            "y",  # add code profile
            "y",  # add tests? (no tests dir)
            "y",  # add docs profile
            "y",  # add git profile
            "y",  # create config
        ],
    ):
        run_interactive(output_dir=".")
    cfg = tmp_path / ".arachna.json"
    if cfg.exists():
        data = json.loads(cfg.read_text())
        assert data["project_name"] == "TestProject"
        assert data["output_dir"] == "out"


def test_run_interactive_defaults_on_enter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# Project")
    with patch(
        "builtins.input",
        side_effect=[
            "",  # default project name
            "",  # default output dir
            "",  # default max tokens
            "y",  # add docs
            "y",  # add git
            "y",  # create
        ],
    ):
        run_interactive(output_dir=".")
