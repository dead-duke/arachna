"""Integration tests for v2.5.0 features — updated for v3.0 CLI."""

import json
import os
import subprocess
import sys


def _arachna(*args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "arachna", *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def test_diff_all_full(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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

    result = _arachna("diff", "--all", "--profile", "code")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "main.py" in content


def test_diff_all_repo_map(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def foo():\n    return 1\n")
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

    result = _arachna("diff", "--all", "--profile", "code", "--mode", "repo-map")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content
    assert "return 1" not in content


def test_diff_all_and_from_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna("diff", "--all", "--from", "some-snap")
    assert result.returncode == 1
    assert "Cannot use --all and --from together" in result.stdout


def test_snapshot_info_full(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
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
                        "pre_commands": ["echo hello"],
                    }
                },
            }
        )
    )

    _arachna("snapshot", "create", "--profile", "code", "--name", "info-e2e")
    result = _arachna("snapshot", "info", "info-e2e")
    assert result.returncode == 0
    assert "Snapshot: info-e2e" in result.stdout
    assert "Profile:" in result.stdout

    result_p = _arachna("snapshot", "info", "info-e2e", "--profile")
    assert result_p.returncode == 0
    assert "directories:" in result_p.stdout

    result_s = _arachna("snapshot", "info", "info-e2e", "--stats")
    assert result_s.returncode == 0
    assert "Files:" in result_s.stdout


def test_snapshot_rename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
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

    _arachna("snapshot", "create", "--profile", "code", "--name", "old-name")
    result = _arachna("snapshot", "rename", "old-name", "new-name")
    assert result.returncode == 0
    assert "renamed" in result.stdout

    lst = _arachna("snapshot", "list")
    assert "new-name" in lst.stdout
    assert "old-name" not in lst.stdout


def test_diff_format_xml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original")
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

    _arachna("snapshot", "create", "--profile", "code", "--name", "xml-e2e")
    (tmp_path / "src" / "main.py").write_text("modified")

    result = _arachna("diff", "--from", "xml-e2e", "--profile", "code", "--format", "xml")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert 'file path="' in content


def test_presets_update_with_url(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna("presets", "update", "--url", "https://example.com/presets.json")
    assert result.returncode == 1
    assert "No presets fetched" in result.stdout


def test_diff_cross_snapshot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("version 1")
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

    _arachna("snapshot", "create", "--profile", "code", "--name", "v1-cross")
    (tmp_path / "src" / "main.py").write_text("version 2")
    _arachna("snapshot", "create", "--profile", "code", "--name", "v2-cross")

    result = _arachna("diff", "--from", "v1-cross", "--to", "v2-cross")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "v1-cross" in content
    assert "v2-cross" in content


def test_diff_flat(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original")
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

    _arachna("snapshot", "create", "--profile", "code", "--name", "flat-e2e")
    (tmp_path / "src" / "main.py").write_text("modified")

    result = _arachna("diff", "--from", "flat-e2e", "--flat")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1


def test_all_mode_headers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import os\n\ndef foo():\n    return 1\n")
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

    result = _arachna("collect", "--all", "--mode", "headers")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "deps:" in content
    assert "exports:" in content


def test_all_query(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "auth.py").write_text("def login(): pass")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass")
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

    result = _arachna("collect", "--all", "--query", "auth")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "auth.py" in content
    assert "utils.py" not in content


def test_profile_mode_repo_map(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def foo():\n    return 1\n\nclass Bar:\n    pass\n")
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

    result = _arachna("collect", "--profile", "code", "--mode", "repo-map")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content
    assert "class Bar:" in content
    assert "return 1" not in content


def test_diff_compress(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original\n\n\n\nspaces")
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

    _arachna("snapshot", "create", "--profile", "code", "--name", "comp-e2e")
    (tmp_path / "src" / "main.py").write_text("modified\n\n\n\nafter")

    result = _arachna("diff", "--from", "comp-e2e", "--profile", "code", "--compress")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "\n\n\n\n" not in content


def test_init_with_preset(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".git").mkdir()

    result = _arachna("init", "--defaults", "--preset", "python")
    assert result.returncode == 0
    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "python" in data["profiles"]
    assert len(data["profiles"]) == 1


def test_diff_mode_structural_integration(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import os\n\ndef foo():\n    return 1\n")
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

    _arachna("snapshot", "create", "--profile", "code", "--name", "struct-int")
    (tmp_path / "src" / "main.py").write_text("import sys\n\ndef foo():\n    return 2\n")

    result = _arachna("diff", "--from", "struct-int", "--profile", "code", "--mode", "structural")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1


def test_profile_query(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "auth.py").write_text("def login(): pass")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass")
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

    result = _arachna("collect", "--profile", "code", "--query", "auth")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "auth.py" in content
    assert "utils.py" not in content


def test_snapshot_update_with_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
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
                    },
                    "alt": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    },
                },
            }
        )
    )

    _arachna("snapshot", "create", "--profile", "code", "--name", "upd-profile")
    result = _arachna("snapshot", "update", "upd-profile", "--profile", "alt")
    assert result.returncode == 0
    assert "updated" in result.stdout


def test_diff_output_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original")
    custom_dir = tmp_path / "custom_diff"
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

    _arachna("snapshot", "create", "--profile", "code", "--name", "od-diff")
    (tmp_path / "src" / "main.py").write_text("modified")

    result = _arachna(
        "diff", "--from", "od-diff", "--profile", "code", "--output-dir", str(custom_dir)
    )
    assert result.returncode == 0
    files = list(custom_dir.glob("chat-diff*"))
    assert len(files) >= 1


def test_diff_all_output_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    custom_dir = tmp_path / "custom_all"
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

    result = _arachna("diff", "--all", "--profile", "code", "--output-dir", str(custom_dir))
    assert result.returncode == 0
    files = list(custom_dir.glob("chat-diff-all*"))
    assert len(files) >= 1


def test_diff_all_query(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "auth.py").write_text("def login(): pass")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass")
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

    result = _arachna("diff", "--all", "--profile", "code", "--query", "auth")
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "auth.py" in content
    assert "utils.py" not in content
