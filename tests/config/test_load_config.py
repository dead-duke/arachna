import json

from arachna.config import load_config


def test_no_file(tmp_path):
    c = load_config(root=tmp_path)
    assert c["project_name"] == "Project"


def test_from_file(tmp_path):
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "X"}))
    assert load_config(root=tmp_path)["project_name"] == "X"
