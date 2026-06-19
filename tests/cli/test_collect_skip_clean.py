"""Tests for skip_clean parameter preventing double manifest cleanup in collect --all."""

from arachna.cli.collect import _cmd_collect_all


def test_collect_all_runs_without_error(tmp_path, make_config):
    """collect --all completes when global clean + per-profile skip_clean work together."""
    config = make_config(
        tmp_path,
        profiles={
            "code": {
                "directories": ["src"],
                "patterns": ["*.py"],
                "max_tokens": 16000,
                "split_mode": "by_file",
                "use_gitignore": False,
            }
        },
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")

    from argparse import Namespace

    args = Namespace(
        profile="code",
        all=True,
        dry_run=False,
        merge=False,
        verbose=False,
        incremental=False,
        compress=False,
        format=None,
        query=None,
        mode="full",
        no_pre_commands=False,
        output_dir=None,
    )
    _cmd_collect_all(args, config)

    files = list((tmp_path / "out").glob("chat-code*.md"))
    assert len(files) == 1


def test_collect_all_with_merge_does_not_skip_clean(tmp_path, make_config):
    """collect --all --merge still uses skip_clean pattern correctly."""
    config = make_config(
        tmp_path,
        profiles={
            "code": {
                "directories": ["src"],
                "patterns": ["*.py"],
                "max_tokens": 16000,
                "split_mode": "by_file",
                "use_gitignore": False,
            }
        },
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")

    from argparse import Namespace

    args = Namespace(
        profile="code",
        all=True,
        dry_run=False,
        merge=True,
        verbose=False,
        incremental=False,
        compress=False,
        format=None,
        query=None,
        mode="full",
        no_pre_commands=False,
        output_dir=None,
    )
    _cmd_collect_all(args, config)

    files = sorted((tmp_path / "out").glob("chat-code_*.md"))
    assert len(files) == 1
    assert "chat-code_1.md" in files[0].name
