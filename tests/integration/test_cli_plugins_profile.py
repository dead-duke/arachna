"""Integration tests for plugins and profile CLI commands."""

import json

from tests.integration.conftest import _arachna


# TC-080: CLI plugins list shows plugin information
def test_plugins_list(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna("plugins", "list")
    assert result.returncode == 0
    assert "Plugins:" in result.stdout


# TC-081: CLI plugins install returns 0 and prints output
def test_plugins_install(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna("plugins", "install", "javascript")
    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0


# TC-082: CLI plugins uninstall returns 0 and prints output
def test_plugins_uninstall(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna("plugins", "uninstall", "tiktoken")
    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0


# TC-083: CLI profile runs benchmark
def test_profile_benchmark(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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

    result = _arachna("profile", "--profile", "code")
    assert result.returncode == 0
    assert "Mode" in result.stdout
    assert "full" in result.stdout


# TC-084: CLI profile --format json
def test_profile_benchmark_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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

    result = _arachna("profile", "--profile", "code", "--format", "json")
    assert result.returncode == 0
    assert "full" in result.stdout


# TC-085: CLI plugins install unknown language
def test_plugins_install_unknown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna("plugins", "install", "unknown_lang")
    assert result.returncode == 0
    assert "Unknown plugin" in result.stdout


# TC-086: CLI plugins uninstall unknown language
def test_plugins_uninstall_unknown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna("plugins", "uninstall", "unknown_lang")
    assert result.returncode == 0
    assert "Unknown plugin" in result.stdout
