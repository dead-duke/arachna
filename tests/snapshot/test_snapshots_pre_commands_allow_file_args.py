from arachna.config.profile_config import ProfileConfig
from arachna.snapshot.diff.snapshot_diff import (
    collect_snapshot_content,
    compute_diff,
    create_snapshot,
)
from arachna.snapshot.store import load_snapshot


def _profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
        exclude_patterns=[],
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_collect_snapshot_content_pre_commands_with_pipes(tmp_path, setup_config):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    p = _profile(pre_commands=["echo 'line1'", "echo 'line2'"])
    files, pre, cmd = collect_snapshot_content(p, root=root)
    assert len(files) == 1
    assert len(pre) == 2
    for hash_spec in pre.values():
        assert hash_spec.startswith("sha256:")


def test_snapshot_create_with_git_pre_commands(tmp_path, setup_config):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (tmp_path / ".git").mkdir()

    p = _profile(pre_commands=["echo 'git log output'", "echo 'tree output'"])
    sid = create_snapshot(p, name="pre-cmd-snap", root=root)
    manifest = load_snapshot(sid, root=root)

    assert "pre_commands" in manifest
    assert len(manifest["pre_commands"]) == 2
    assert "files" in manifest


def test_diff_with_pre_commands_current_state(tmp_path, setup_config):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    p1 = _profile(pre_commands=["echo 'version 1'"])
    sid = create_snapshot(p1, name="diff-pre-snap", root=root)

    p2 = _profile(pre_commands=["echo 'version 2'"])
    diffs = compute_diff(sid, p2, root=root)
    pre_diffs = [d for d in diffs if d.path and d.path.startswith("pre:")]
    assert len(pre_diffs) >= 1
