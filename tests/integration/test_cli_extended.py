"""Extended integration tests for CLI coverage gaps."""

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


# TC-045: --completion bash
def test_completion_bash():
    """TC-045: arachna --completion bash prints completion script."""
    result = _arachna("--completion", "bash")
    assert result.returncode == 0
    assert "complete -F _arachna_complete arachna" in result.stdout


# TC-046: --completion zsh
def test_completion_zsh():
    """TC-046: arachna --completion zsh prints completion script."""
    result = _arachna("--completion", "zsh")
    assert result.returncode == 0
    assert "#compdef arachna" in result.stdout


# TC-047: --validate with multiple profiles (one invalid)
def test_validate_multi_profile(tmp_path, monkeypatch):
    """TC-047: --validate with multiple profiles exits 1 when one is invalid."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "good": {"directories": ["src"], "max_tokens": 100, "split_mode": "by_file"},
                    "bad": {"max_tokens": 0},
                }
            }
        )
    )

    result = _arachna("--validate")
    assert result.returncode == 1
    assert "bad" in result.stdout


# TC-048: --init interactive via CLI
def test_init_interactive_cli(tmp_path, monkeypatch):
    """TC-048: --init runs interactive mode and creates config."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".git").mkdir()

    # Use defaults to avoid stdin dependency
    result = _arachna("--init", "--defaults")
    assert result.returncode == 0
    assert (tmp_path / ".arachna.json").exists()


# TC-049: --install-hook --force
def test_install_hook_force(tmp_path, monkeypatch):
    """TC-049: --install-hook --force overwrites existing hook."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    # First install
    result1 = _arachna("--install-hook")
    assert result1.returncode == 0

    # Second install with --force
    result2 = _arachna("--install-hook", "--force")
    assert result2.returncode == 0

    hook = tmp_path / ".git" / "hooks" / "post-commit"
    assert hook.exists()
    assert "arachna --all" in hook.read_text()


# TC-050: --all --dry-run
def test_all_dry_run(tmp_path, monkeypatch):
    """TC-050: --all --dry-run shows all profiles without writing."""
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
                    "cmd": {
                        "command": "echo hi",
                        "max_tokens": 100,
                        "split_mode": "by_file",
                    },
                },
            }
        )
    )

    result = _arachna("--all", "--dry-run")
    assert result.returncode == 0
    assert "[code] section" in result.stdout
    assert "[cmd] section" in result.stdout

    out_dir = tmp_path / "out"
    if out_dir.exists():
        files = list(out_dir.glob("chat-*"))
        assert len(files) == 0


# TC-051: --format json --all
def test_format_json_all(tmp_path, monkeypatch):
    """TC-051: --format json --all produces JSON output for all profiles."""
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

    result = _arachna("--all", "--format", "json")
    assert result.returncode == 0

    out_dir = tmp_path / "out"
    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert '"path":' in content
    assert '"content":' in content


# TC-052: --profile with --merge and --dry-run
def test_merge_dry_run(tmp_path, monkeypatch):
    """TC-052: --profile X --merge --dry-run previews without writing."""
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

    result = _arachna("--profile", "code", "--merge", "--dry-run")
    assert result.returncode == 0
    assert "main.py" in result.stdout

    out_dir = tmp_path / "out"
    if out_dir.exists():
        files = list(out_dir.glob("chat-code*"))
        assert len(files) == 0
