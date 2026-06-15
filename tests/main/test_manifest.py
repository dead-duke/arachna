"""Tests for arachna manifest command."""

import json

from arachna.cli.manifest import _cmd_manifest


def _args(json_flag=False, output_dir=None):
    from argparse import Namespace

    return Namespace(json=json_flag, output_dir=output_dir)


def test_manifest_text_output(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    out = tmp_path / "out"
    out.mkdir()

    from argparse import Namespace

    from arachna.cli.collect import _cmd_collect_profile

    _cmd_collect_profile(
        Namespace(
            profile="code",
            all=False,
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
        ),
        config,
    )

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_manifest(_args(), config)
    sys.stdout = old
    output = out.getvalue()
    assert "MANIFEST" in output
    assert "chat-code" in output


def test_manifest_json_output(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    out = tmp_path / "out"
    out.mkdir()

    from argparse import Namespace

    from arachna.cli.collect import _cmd_collect_profile

    _cmd_collect_profile(
        Namespace(
            profile="code",
            all=False,
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
        ),
        config,
    )

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_manifest(_args(json_flag=True), config)
    sys.stdout = old
    output = out.getvalue()
    data = json.loads(output)
    assert data["project_name"] == "test"
    assert "profiles" in data
    assert "parts" in data
    assert len(data["parts"]) >= 1
    assert "file" in data["parts"][0]
    assert "tokens" in data["parts"][0]


def test_manifest_empty(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "out").mkdir()

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_manifest(_args(), config)
    sys.stdout = old
    assert "No collected files found" in out.getvalue()
