from io import StringIO

from arachna.cli.collect import _cmd_collect_all, _cmd_collect_profile


def _args(profile="code", all=False, dry_run=True):
    from argparse import Namespace

    return Namespace(
        profile=profile,
        all=all,
        dry_run=dry_run,
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


def test_dry_run_profile_no_files_created(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    ctx = tmp_path / "out"
    import sys

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_collect_profile(_args(), config)
    sys.stdout = old
    output = out.getvalue()
    assert "main.py" in output
    assert not ctx.exists() or not list(ctx.glob("chat-code*.md"))


def test_dry_run_all_output(tmp_path, make_config):
    config = make_config(tmp_path, profiles={"a": {"command": "echo hi", "max_tokens": 100}})
    import sys

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_collect_all(_args(all=True), config)
    sys.stdout = old
    output = out.getvalue()
    assert "[a] section" in output


def test_dry_run_empty_profile(tmp_path, make_config):
    config = make_config(
        tmp_path, profiles={"empty": {"directories": ["nonexistent"], "max_tokens": 100}}
    )
    import sys

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_collect_profile(_args(profile="empty"), config)
    sys.stdout = old
    output = out.getvalue()
    assert "section" in output


def test_dry_run_single_profile(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    ctx = tmp_path / "out"
    import sys

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_collect_profile(_args(), config)
    sys.stdout = old
    output = out.getvalue()
    assert "main.py" in output
    assert not ctx.exists() or not list(ctx.glob("chat-code*.md"))
