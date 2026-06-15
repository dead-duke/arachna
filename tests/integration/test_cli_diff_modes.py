import json

from tests.integration.conftest import _arachna


def test_diff_mode_structural(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "struct-snap", cwd=tmp_path)
    (src / "main.py").write_text("def foo():\n    return 2\n")
    result = _arachna(
        "diff", "--from", "struct-snap", "--profile", "code", "--mode", "structural", cwd=tmp_path
    )
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1


def test_diff_mode_repo_map(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n\ndef bar():\n    return 2\n")
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "rm-snap", cwd=tmp_path)
    (src / "main.py").write_text("def foo():\n    return 3\n\ndef bar():\n    return 4\n")
    result = _arachna(
        "diff", "--from", "rm-snap", "--profile", "code", "--mode", "repo-map", cwd=tmp_path
    )
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1


def test_diff_mode_structural_no_changes(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "nochg-snap", cwd=tmp_path)
    result = _arachna(
        "diff", "--from", "nochg-snap", "--profile", "code", "--mode", "structural", cwd=tmp_path
    )
    assert result.returncode == 0
