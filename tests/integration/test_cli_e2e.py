"""End-to-end integration tests — run arachna as a real process."""

import json
import subprocess
import sys


def _arachna(*args: str) -> subprocess.CompletedProcess:
    """Run arachna as subprocess, return CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "arachna", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_version():
    """TC-040: arachna --version prints version and exits 0."""
    result = _arachna("--version")
    assert result.returncode == 0
    assert "arachna v" in result.stdout


def test_list():
    """TC-014: arachna --list prints profiles."""
    result = _arachna("--list")
    assert result.returncode == 0
    assert "full:" in result.stdout


def test_validate():
    """TC-012: arachna --validate exits 0 on valid config."""
    result = _arachna("--validate")
    assert result.returncode == 0
    assert "valid" in result.stdout


def test_collect_and_clean(tmp_path, monkeypatch):
    """TC-001, TC-004: collect a profile, verify output, clean."""
    monkeypatch.chdir(tmp_path)

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

    result = _arachna("--profile", "code")
    assert result.returncode == 0

    out_dir = tmp_path / "out"
    files = sorted(out_dir.glob("chat-code*"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "main.py" in content
    assert "print('hello')" in content

    result = _arachna("--clean")
    assert result.returncode == 0
    remaining = list(out_dir.glob("chat-code*"))
    assert len(remaining) == 0


def test_dry_run_no_files(tmp_path, monkeypatch):
    """TC-003: --dry-run prints stats, creates no files."""
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

    result = _arachna("--profile", "code", "--dry-run")
    assert result.returncode == 0
    assert "main.py" in result.stdout

    out_dir = tmp_path / "out"
    if out_dir.exists():
        files = list(out_dir.glob("chat-code*"))
        assert len(files) == 0


def test_missing_profile_exits_1(tmp_path, monkeypatch):
    """Non-existent profile exits with 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"code": {"command": "echo hi", "max_tokens": 100}}})
    )

    result = _arachna("--profile", "nonexistent")
    assert result.returncode == 1


def test_collect_all(tmp_path, monkeypatch):
    """TC-002: --all collects all profiles."""
    monkeypatch.chdir(tmp_path)

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

    result = _arachna("--all")
    assert result.returncode == 0

    out_dir = tmp_path / "out"
    code_files = list(out_dir.glob("chat-code*"))
    docs_files = list(out_dir.glob("chat-docs*"))
    manifest = out_dir / "chat-manifest.md"
    assert len(code_files) >= 1
    assert len(docs_files) >= 1
    assert manifest.exists()


def test_compress_flag(tmp_path, monkeypatch):
    """TC-011: --compress collapses blank lines."""
    monkeypatch.chdir(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("a\n\n\n\nb\n")
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

    result = _arachna("--profile", "code", "--compress")
    assert result.returncode == 0

    out_dir = tmp_path / "out"
    files = list(out_dir.glob("chat-code*"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "\n\n\n\n" not in content


def test_doctor_valid(tmp_path, monkeypatch):
    """TC-015: --doctor exits 0 on valid config."""
    monkeypatch.chdir(tmp_path)

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

    result = _arachna("--doctor")
    assert result.returncode == 0
    assert "All profiles valid" in result.stdout


def test_install_hook(tmp_path, monkeypatch):
    """TC-023: --install-hook creates post-commit hook."""
    monkeypatch.chdir(tmp_path)

    (tmp_path / ".git").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    result = _arachna("--install-hook")
    assert result.returncode == 0

    hook = tmp_path / ".git" / "hooks" / "post-commit"
    assert hook.exists()
    assert "arachna --all" in hook.read_text()


def test_merge_mode(tmp_path, monkeypatch):
    """TC-025: --merge appends to existing output."""
    monkeypatch.chdir(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("print('hi')")
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

    _arachna("--profile", "code", "--merge")
    _arachna("--profile", "code", "--merge")

    out_dir = tmp_path / "out"
    files = sorted(out_dir.glob("chat-code_*.md"))
    assert len(files) == 2
    assert "chat-code_1.md" in files[0].name
    assert "chat-code_2.md" in files[1].name


def test_gitignore_excludes(tmp_path, monkeypatch):
    """TC-033: .gitignore patterns exclude files from collection."""
    monkeypatch.chdir(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "debug.txt").write_text("log")
    (tmp_path / ".gitignore").write_text("*.txt\n")
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

    result = _arachna("--profile", "code")
    assert result.returncode == 0

    out_dir = tmp_path / "out"
    files = list(out_dir.glob("chat-code*"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "main.py" in content
    assert "debug.txt" not in content


def test_init_defaults(tmp_path, monkeypatch):
    """TC-017: --init --defaults creates config with detected profiles."""
    monkeypatch.chdir(tmp_path)

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".git").mkdir()

    result = _arachna("--init", "--defaults")
    assert result.returncode == 0

    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "python" in data["profiles"]
    assert "git" in data["profiles"]
