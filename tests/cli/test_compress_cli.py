from arachna.cli.collect import _cmd_collect_profile


def _args(compress=False):
    from argparse import Namespace

    return Namespace(
        profile="code",
        all=False,
        dry_run=False,
        merge=False,
        verbose=False,
        incremental=False,
        compress=compress,
        format=None,
        query=None,
        mode="full",
        no_pre_commands=False,
        output_dir=None,
    )


def test_compress_cli(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("a\n\n\n\nb\n")
    _cmd_collect_profile(_args(compress=True), config)
    files = list((tmp_path / "out").glob("chat-code*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "\n\n\n\n" not in content


def test_compress_cli_no_flag(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("a\n\n\n\nb\n")
    _cmd_collect_profile(_args(compress=False), config)
    files = list((tmp_path / "out").glob("chat-code*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert content.count("\n\n\n\n") >= 1
