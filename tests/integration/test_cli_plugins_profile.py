"""Integration tests for plugins and profile CLI commands."""

import json

from tests.integration.conftest import _arachna


def test_plugins_list(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("plugins", "list", cwd=tmp_path)
    assert result.returncode == 0
    assert "Plugins:" in result.stdout


def test_plugins_install(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("plugins", "install", "javascript", cwd=tmp_path)
    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0


def test_plugins_uninstall(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("plugins", "uninstall", "tiktoken", cwd=tmp_path)
    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0


def test_profile_benchmark(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
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

    result = _arachna("profile", "--profile", "code", cwd=tmp_path)
    assert result.returncode == 0
    assert "Mode" in result.stdout
    assert "full" in result.stdout


def test_profile_benchmark_json(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
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

    result = _arachna("profile", "--profile", "code", "--format", "json", cwd=tmp_path)
    assert result.returncode == 0
    assert "full" in result.stdout


def test_plugins_install_unknown(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("plugins", "install", "unknown_lang", cwd=tmp_path)
    assert result.returncode == 0
    assert "Unknown plugin" in result.stdout


def test_plugins_uninstall_unknown(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("plugins", "uninstall", "unknown_lang", cwd=tmp_path)
    assert result.returncode == 0
    assert "Unknown plugin" in result.stdout
