"""Integration test: full cycle with explicit root via config."""

import json

from tests.integration.conftest import _arachna


def test_full_cycle_with_root(tmp_path):
    """TC-195: collect -> snapshot create -> modify -> diff -> snapshot update -> diff (no changes)."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('v1')")
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

    # Collect
    r1 = _arachna("collect", "--profile", "code", cwd=tmp_path)
    assert r1.returncode == 0
    files = list(out_dir.glob("chat-code*"))
    assert len(files) == 1

    # Create snapshot at v1
    r2 = _arachna("snapshot", "create", "--profile", "code", "--name", "cycle-test", cwd=tmp_path)
    assert r2.returncode == 0
    assert "cycle-test" in r2.stdout

    # Modify file
    (tmp_path / "src" / "main.py").write_text("print('v2')")

    # Diff from v1 — should see changes
    r3 = _arachna("diff", "--from", "cycle-test", "--profile", "code", cwd=tmp_path)
    assert r3.returncode == 0
    diff_files = list(out_dir.glob("chat-diff*"))
    assert len(diff_files) >= 1
    content = diff_files[0].read_text()
    assert "REMOVED" in content or "ADDED" in content

    # Update snapshot to v2
    r4 = _arachna("snapshot", "update", "cycle-test", "--profile", "code", cwd=tmp_path)
    assert r4.returncode == 0

    # Diff from updated snapshot — no changes
    r5 = _arachna("diff", "--from", "cycle-test", "--profile", "code", cwd=tmp_path)
    assert r5.returncode == 0
