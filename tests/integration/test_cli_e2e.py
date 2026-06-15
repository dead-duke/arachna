"""End-to-end integration tests — run arachna as a real process."""

import json

from tests.integration.conftest import _arachna


def test_version():
    result = _arachna("--version")
    assert result.returncode == 0
    assert "arachna v" in result.stdout


def test_list(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("collect", "--list", cwd=tmp_path)
    assert result.returncode == 0
    assert "default:" in result.stdout


def test_validate(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                    }
                }
            }
        )
    )
    result = _arachna("collect", "--validate", cwd=tmp_path)
    assert result.returncode == 0
    assert "valid" in result.stdout


def test_collect_and_clean(tmp_path):
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

    result = _arachna("collect", "--profile", "code", cwd=tmp_path)
    assert result.returncode == 0

    files = sorted(out_dir.glob("chat-code*"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "main.py" in content
    assert "print('hello')" in content

    result = _arachna("collect", "--clean", cwd=tmp_path)
    assert result.returncode == 0
    remaining = list(out_dir.glob("chat-code*"))
    assert len(remaining) == 0


def test_dry_run_no_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
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

    result = _arachna("collect", "--profile", "code", "--dry-run", cwd=tmp_path)
    assert result.returncode == 0
    assert "main.py" in result.stdout

    if out_dir.exists():
        files = list(out_dir.glob("chat-code*"))
        assert len(files) == 0


def test_missing_profile_exits_1(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"code": {"command": "echo hi", "max_tokens": 100}}})
    )
    result = _arachna("collect", "--profile", "nonexistent", cwd=tmp_path)
    assert result.returncode == 1


def test_collect_all(tmp_path):
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
                    },
                    "docs": {
                        "files": [],
                        "directories": [],
                        "pre_commands": ["echo doc"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    },
                },
            }
        )
    )

    result = _arachna("collect", "--all", cwd=tmp_path)
    assert result.returncode == 0

    code_files = list(out_dir.glob("chat-code*"))
    docs_files = list(out_dir.glob("chat-docs*"))
    manifest = out_dir / "chat-manifest.md"
    assert len(code_files) >= 1
    assert len(docs_files) >= 1
    assert manifest.exists()


def test_compress_flag(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("a\n\n\n\nb\n")
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

    result = _arachna("collect", "--profile", "code", "--compress", cwd=tmp_path)
    assert result.returncode == 0

    files = list(out_dir.glob("chat-code*"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "\n\n\n\n" not in content


def test_doctor_valid(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                    }
                }
            }
        )
    )
    result = _arachna("doctor", cwd=tmp_path)
    assert result.returncode == 0
    assert "All profiles valid" in result.stdout


def test_install_hook(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))
    result = _arachna("init", "--install-hook", cwd=tmp_path)
    assert result.returncode == 0
    hook = tmp_path / ".git" / "hooks" / "post-commit"
    assert hook.exists()
    assert "arachna collect --all" in hook.read_text()


def test_merge_mode(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("print('hi')")
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

    _arachna("collect", "--profile", "code", "--merge", cwd=tmp_path)
    _arachna("collect", "--profile", "code", "--merge", cwd=tmp_path)

    files = sorted(out_dir.glob("chat-code_*.md"))
    assert len(files) == 2
    assert "chat-code_1.md" in files[0].name
    assert "chat-code_2.md" in files[1].name


def test_gitignore_excludes(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "debug.txt").write_text("log")
    (tmp_path / ".gitignore").write_text("*.txt\n")
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
                        "patterns": ["*"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": True,
                    }
                },
            }
        )
    )

    result = _arachna("collect", "--profile", "code", cwd=tmp_path)
    assert result.returncode == 0

    files = list(out_dir.glob("chat-code*"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "main.py" in content
    assert "debug.txt" not in content


def test_init_defaults(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".git").mkdir()

    result = _arachna("init", "--defaults", cwd=tmp_path)
    assert result.returncode == 0

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "python" in data["profiles"]
    assert "git" in data["profiles"]


def test_verbose_flag(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "data.bin").write_bytes(b"\x00\x01\x02")
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
                        "patterns": ["*"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    result = _arachna("collect", "--profile", "code", "--verbose", cwd=tmp_path)
    assert result.returncode == 0
    assert "Skipped" in result.stdout or "Skipped" in result.stderr


def test_incremental_flag(tmp_path):
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

    result1 = _arachna("collect", "--profile", "code", "--incremental", cwd=tmp_path)
    assert result1.returncode == 0

    files_after_first = sorted(out_dir.glob("chat-code*"))
    assert len(files_after_first) == 1

    result2 = _arachna("collect", "--profile", "code", "--incremental", cwd=tmp_path)
    assert result2.returncode == 0
    assert "No content collected" in result2.stdout


def test_output_dir_flag(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
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

    custom_dir = tmp_path / "custom_output"
    result = _arachna("collect", "--profile", "code", "--output-dir", str(custom_dir), cwd=tmp_path)
    assert result.returncode == 0

    assert custom_dir.is_dir()
    custom_files = list(custom_dir.glob("chat-code*"))
    assert len(custom_files) == 1

    default_out = tmp_path / "out"
    assert not default_out.exists() or len(list(default_out.glob("chat-code*"))) == 0
