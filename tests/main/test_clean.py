import json

from arachna.cli.collect import _cmd_collect_clean


def _args(output_dir=None):
    from argparse import Namespace

    return Namespace(output_dir=output_dir)


def test_clean_numbered(tmp_path, make_config):
    config = make_config(tmp_path)
    ctx = tmp_path / "out"
    ctx.mkdir()
    (ctx / "chat-c_1.md").write_text("x")
    _cmd_collect_clean(_args(), config)
    assert not (ctx / "chat-c_1.md").exists()


def test_clean_plain(tmp_path, make_config):
    config = make_config(tmp_path)
    ctx = tmp_path / "out"
    ctx.mkdir()
    (ctx / "chat-c.md").write_text("x")
    _cmd_collect_clean(_args(), config)
    assert not (ctx / "chat-c.md").exists()


def test_clean_via_manifest(tmp_path, make_config):
    config = make_config(tmp_path, profiles={"x": {"command": "echo hi", "max_tokens": 100}})
    ctx = tmp_path / "out"
    ctx.mkdir()
    mf = ctx / ".arachna_manifest.json"
    mf.write_text(json.dumps({"files": ["chat-x.md"]}))
    (ctx / "chat-x.md").write_text("data")
    _cmd_collect_clean(_args(), config)
    assert not (ctx / "chat-x.md").exists()
    assert not mf.exists()
