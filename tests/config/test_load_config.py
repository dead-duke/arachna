import json
from unittest.mock import patch

from arachna.config import load_config


def test_no_file():
    with patch("arachna.config.find_config", return_value=None):
        c = load_config()
        assert c["project_name"] == "Project"


def test_from_file(tmp_path, monkeypatch):
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "X"}))
    monkeypatch.chdir(tmp_path)
    assert load_config()["project_name"] == "X"
