"""Coverage for __main__.py uncovered branches — updated for v3.0 subparser CLI."""

import json
from argparse import Namespace
from unittest.mock import patch

from arachna.__main__ import (
    _cmd_collect_clean,
    _cmd_collect_list,
    _cmd_collect_validate,
    _list_profiles,
    _print_collected,
    _write_manifest,
)


def test_list_profiles_empty_config():
    """_list_profiles with empty profiles returns ['default']."""
    assert _list_profiles({"profiles": {}}) == ["default"]


def test_list_profiles_no_key():
    """_list_profiles without profiles key returns ['default']."""
    assert _list_profiles({}) == ["default"]


def test_print_collected_empty():
    """_print_collected with empty list prints 'No content collected'."""
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _print_collected([])
    sys.stdout = old
    assert "No content collected" in out.getvalue()


def test_print_collected_with_files(tmp_path, monkeypatch):
    """_print_collected with files prints file info."""
    import sys
    from io import StringIO

    monkeypatch.chdir(tmp_path)
    f = tmp_path / "chat-c.md"
    f.write_text("hello world")

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _print_collected([str(f)])
    sys.stdout = old
    assert "chat-c.md" in out.getvalue()


def test_write_manifest(tmp_path):
    """_write_manifest creates chat-manifest.md."""
    out = tmp_path / "out"
    out.mkdir()
    f1 = str(out / "chat-c.md")
    (out / "chat-c.md").write_text("content")

    _write_manifest(out, [f1], {f1: 10}, {"project_name": "Test"})

    mf = out / "chat-manifest.md"
    assert mf.exists()
    content = mf.read_text()
    assert "Test" in content
    assert "chat-c.md" in content


def test_cmd_clean_corrupted_manifest(tmp_path, monkeypatch):
    """_cmd_collect_clean handles corrupted manifest JSON."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    ctx = tmp_path / "arachna_context"
    ctx.mkdir()
    (ctx / ".arachna_manifest.json").write_text("not json")

    _cmd_collect_clean(Namespace(output_dir=None), {})


def test_cmd_clean_manifest_os_error(tmp_path, monkeypatch):
    """_cmd_collect_clean handles OSError reading manifest."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    ctx = tmp_path / "arachna_context"
    ctx.mkdir()
    (ctx / ".arachna_manifest.json").write_text('{"files": ["chat-c.md"]}')

    with patch("pathlib.Path.read_text", side_effect=OSError("disk error")):
        _cmd_collect_clean(Namespace(output_dir=None), {})


def test_cmd_validate_multiple_profiles(tmp_path, monkeypatch):
    """_cmd_collect_validate with multiple profiles — one valid, one invalid."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "good": {"directories": ["src"], "max_tokens": 100},
                    "bad": {"max_tokens": 0},
                }
            }
        )
    )
    config = json.loads((tmp_path / ".arachna.json").read_text())

    with patch("sys.exit") as mock_exit:
        _cmd_collect_validate(Namespace(), config)
        mock_exit.assert_called_with(1)


def test_cmd_list_keyerror(tmp_path, monkeypatch):
    """_cmd_collect_list handles KeyError from get_profile."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {"c": {"max_tokens": 100}}}))
    config = json.loads((tmp_path / ".arachna.json").read_text())

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_collect_list(Namespace(), config)
    sys.stdout = old
