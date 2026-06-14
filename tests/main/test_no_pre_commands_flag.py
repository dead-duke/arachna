from arachna.cli.collect import _cmd_collect_profile


def _args(profile="code", no_pre_commands=False):
    from argparse import Namespace

    return Namespace(
        profile=profile,
        all=False,
        dry_run=False,
        merge=False,
        verbose=False,
        incremental=False,
        compress=False,
        format=None,
        query=None,
        mode="full",
        no_pre_commands=no_pre_commands,
        output_dir=None,
    )


def test_no_pre_commands_flag(tmp_path, make_config):
    config = make_config(
        tmp_path,
        profiles={
            "code": {
                "directories": ["src"],
                "patterns": ["*.py"],
                "max_tokens": 16000,
                "split_mode": "by_file",
                "use_gitignore": False,
                "pre_commands": ["echo 'TREE OUTPUT'"],
            }
        },
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    _cmd_collect_profile(_args(no_pre_commands=True), config)
    files = list((tmp_path / "out").glob("chat-code*"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "main.py" in content
    assert "TREE OUTPUT" not in content


def test_no_pre_commands_without_flag_shows_output(tmp_path, make_config):
    config = make_config(
        tmp_path,
        profiles={
            "code": {
                "directories": ["src"],
                "patterns": ["*.py"],
                "max_tokens": 16000,
                "split_mode": "by_file",
                "use_gitignore": False,
                "pre_commands": ["echo 'TREE OUTPUT'"],
            }
        },
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    _cmd_collect_profile(_args(no_pre_commands=False), config)
    files = list((tmp_path / "out").glob("chat-code*"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "TREE OUTPUT" in content
