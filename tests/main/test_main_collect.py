from arachna.cli.collect import _cmd_collect_all, _cmd_collect_profile


def _args(all=False):
    from argparse import Namespace

    return Namespace(
        profile="code",
        all=all,
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


def test_collect_profile(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    _cmd_collect_profile(_args(), config)
    files = list((tmp_path / "out").glob("chat-code*.md"))
    assert len(files) == 1


def test_collect_all(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    _cmd_collect_all(_args(all=True), config)
    files = list((tmp_path / "out").glob("chat-code*.md"))
    assert len(files) == 1


def test_no_profiles_default(tmp_path, make_config):
    config = make_config(tmp_path)
    config["profiles"] = {}
    (tmp_path / "main.py").write_text("print('hi')")
    _cmd_collect_all(_args(all=True), config)
    files = list((tmp_path / "out").glob("chat-default*.md"))
    assert len(files) == 1
