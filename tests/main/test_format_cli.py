from arachna.cli.collect import _cmd_collect_profile


def _args(fmt=None):
    from argparse import Namespace

    return Namespace(
        profile="code",
        all=False,
        dry_run=False,
        merge=False,
        verbose=False,
        incremental=False,
        compress=False,
        format=fmt,
        query=None,
        mode="full",
        no_pre_commands=False,
        output_dir=None,
    )


def test_format_xml(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    _cmd_collect_profile(_args(fmt="xml"), config)
    files = list((tmp_path / "out").glob("chat-code*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert '<file path="' in content
    assert "<![CDATA[" in content


def test_format_json(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    _cmd_collect_profile(_args(fmt="json"), config)
    files = list((tmp_path / "out").glob("chat-code*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert '"path":' in content
    assert '"content":' in content


def test_format_default_is_markdown(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    _cmd_collect_profile(_args(), config)
    files = list((tmp_path / "out").glob("chat-code*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "```python" in content
