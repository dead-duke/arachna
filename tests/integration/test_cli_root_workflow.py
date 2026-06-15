import json

from tests.integration.conftest import _arachna


def test_collect_with_explicit_config(tmp_path):
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
    r = _arachna("collect", "--profile", "code", cwd=tmp_path)
    assert r.returncode == 0
    files = list((tmp_path / "out").glob("chat-code*"))
    assert len(files) == 1


def test_snapshot_workflow_in_isolation(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("v1")
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
    r1 = _arachna("snapshot", "create", "--profile", "code", "--name", "iso-snap", cwd=tmp_path)
    assert r1.returncode == 0
    r2 = _arachna("snapshot", "list", cwd=tmp_path)
    assert r2.returncode == 0
    assert "iso-snap" in r2.stdout
    r3 = _arachna("snapshot", "info", "iso-snap", cwd=tmp_path)
    assert r3.returncode == 0
    assert "iso-snap" in r3.stdout
    r4 = _arachna("snapshot", "delete", "iso-snap", cwd=tmp_path)
    assert r4.returncode == 0
    r5 = _arachna("snapshot", "list", cwd=tmp_path)
    assert "iso-snap" not in r5.stdout


def test_diff_workflow_in_isolation(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original")
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "diff-snap", cwd=tmp_path)
    (tmp_path / "src" / "main.py").write_text("modified")
    r = _arachna("diff", "--from", "diff-snap", "--profile", "code", cwd=tmp_path)
    assert r.returncode == 0
    files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(files) >= 1


def test_store_workflow_in_isolation(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("hello")
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "store-snap", cwd=tmp_path)
    r1 = _arachna("store", "stats", cwd=tmp_path)
    assert r1.returncode == 0
    assert "Snapshots:" in r1.stdout
    r2 = _arachna("store", "gc", cwd=tmp_path)
    assert r2.returncode == 0


def test_init_install_hook_command(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))
    r = _arachna("init", "--install-hook", cwd=tmp_path)
    assert r.returncode == 0
    hook = tmp_path / ".git" / "hooks" / "post-commit"
    assert hook.exists()
    content = hook.read_text()
    assert "arachna collect --all" in content
