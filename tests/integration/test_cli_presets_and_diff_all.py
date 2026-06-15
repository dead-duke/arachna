import json

from tests.integration.conftest import _arachna


def test_diff_all_full(tmp_path):
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
    result = _arachna("diff", "--all", "--profile", "code", cwd=tmp_path)
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "main.py" in content


def test_diff_all_repo_map(tmp_path):
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
    result = _arachna("diff", "--all", "--profile", "code", "--mode", "repo-map", cwd=tmp_path)
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content
    assert "return 1" not in content


def test_diff_all_and_from_error(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("diff", "--all", "--from", "some-snap", cwd=tmp_path)
    assert result.returncode == 1
    assert "Cannot use --all and --from together" in result.stdout


def test_snapshot_info_full(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "info-e2e", cwd=tmp_path)
    result = _arachna("snapshot", "info", "info-e2e", cwd=tmp_path)
    assert result.returncode == 0
    assert "Snapshot: info-e2e" in result.stdout
    assert "Profile:" in result.stdout


def test_snapshot_rename(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "old-name", cwd=tmp_path)
    result = _arachna("snapshot", "rename", "old-name", "new-name", cwd=tmp_path)
    assert result.returncode == 0
    assert "renamed" in result.stdout
    lst = _arachna("snapshot", "list", cwd=tmp_path)
    assert "new-name" in lst.stdout
    assert "old-name" not in lst.stdout


def test_diff_format_xml(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "xml-e2e", cwd=tmp_path)
    (tmp_path / "src" / "main.py").write_text("modified")
    result = _arachna(
        "diff", "--from", "xml-e2e", "--profile", "code", "--format", "xml", cwd=tmp_path
    )
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert 'file path="' in content


def test_presets_update_with_url(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna(
        "presets", "update", "--url", "https://example.com/presets.json", cwd=tmp_path
    )
    assert result.returncode == 1
    assert "No presets fetched" in result.stdout


def test_diff_cross_snapshot(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "v1-cross", cwd=tmp_path)
    (tmp_path / "src" / "main.py").write_text("version 2")
    _arachna("snapshot", "create", "--profile", "code", "--name", "v2-cross", cwd=tmp_path)
    result = _arachna("diff", "--from", "v1-cross", "--to", "v2-cross", cwd=tmp_path)
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "v1-cross" in content
    assert "v2-cross" in content


def test_diff_flat(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "flat-e2e", cwd=tmp_path)
    (tmp_path / "src" / "main.py").write_text("modified")
    result = _arachna("diff", "--from", "flat-e2e", "--flat", cwd=tmp_path)
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1


def test_all_mode_headers(tmp_path):
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
    result = _arachna("collect", "--all", "--mode", "headers", cwd=tmp_path)
    assert result.returncode == 0
    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "deps:" in content
    assert "exports:" in content


def test_all_query(tmp_path):
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
    result = _arachna("collect", "--all", "--query", "auth", cwd=tmp_path)
    assert result.returncode == 0
    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "auth.py" in content
    assert "utils.py" not in content


def test_profile_mode_repo_map(tmp_path):
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
    result = _arachna("collect", "--profile", "code", "--mode", "repo-map", cwd=tmp_path)
    assert result.returncode == 0
    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content
    assert "class Bar:" in content
    assert "return 1" not in content


def test_diff_compress(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "comp-e2e", cwd=tmp_path)
    (tmp_path / "src" / "main.py").write_text("modified\n\n\n\nafter")
    result = _arachna("diff", "--from", "comp-e2e", "--profile", "code", "--compress", cwd=tmp_path)
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "\n\n\n\n" not in content


def test_init_with_preset(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".git").mkdir()
    result = _arachna("init", "--defaults", "--preset", "python", cwd=tmp_path)
    assert result.returncode == 0
    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "python" in data["profiles"]
    assert len(data["profiles"]) == 1


def test_diff_mode_structural_integration(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "struct-int", cwd=tmp_path)
    (tmp_path / "src" / "main.py").write_text("import sys\n\ndef foo():\n    return 2\n")
    result = _arachna(
        "diff", "--from", "struct-int", "--profile", "code", "--mode", "structural", cwd=tmp_path
    )
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1


def test_profile_query(tmp_path):
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
    result = _arachna("collect", "--profile", "code", "--query", "auth", cwd=tmp_path)
    assert result.returncode == 0
    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "auth.py" in content
    assert "utils.py" not in content


def test_snapshot_update_with_profile(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "upd-profile", cwd=tmp_path)
    result = _arachna("snapshot", "update", "upd-profile", "--profile", "alt", cwd=tmp_path)
    assert result.returncode == 0
    assert "updated" in result.stdout
