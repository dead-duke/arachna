"""Integration tests for arachna manifest --json."""

import json

from tests.integration.conftest import _arachna


def test_manifest_json_output(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    _arachna("collect", "--profile", "code", cwd=tmp_path)
    result = _arachna("manifest", "--json", cwd=tmp_path)
    assert result.returncode == 0

    data = json.loads(result.stdout)
    assert data["project_name"] == "test"
    assert "profiles" in data
    assert "parts" in data
    assert len(data["parts"]) >= 1
    assert "file" in data["parts"][0]
    assert "tokens" in data["parts"][0]


def test_manifest_json_empty(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = _arachna("manifest", "--json", cwd=tmp_path)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["parts"] == []


def test_manifest_text_output(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    _arachna("collect", "--profile", "code", cwd=tmp_path)
    result = _arachna("manifest", cwd=tmp_path)
    assert result.returncode == 0
    assert "MANIFEST" in result.stdout
    assert "chat-code" in result.stdout
