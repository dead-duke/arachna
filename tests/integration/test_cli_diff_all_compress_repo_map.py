import json

from tests.integration.conftest import _arachna


def test_diff_all_compress_repo_map(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def foo():\n\n\n\n    return 1\n")
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
    result = _arachna(
        "diff", "--all", "--profile", "code", "--compress", "--mode", "repo-map", cwd=tmp_path
    )
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff-all*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content
    assert "return 1" not in content
    assert "\n\n\n\n" not in content
