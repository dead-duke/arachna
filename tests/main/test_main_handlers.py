"""Coverage for __main__.py uncovered branches."""

import json
from argparse import Namespace
from unittest.mock import patch

import pytest

from arachna.__main__ import (
    _cmd_clean,
    _cmd_dry_run,
    _cmd_list,
    _cmd_single,
    _cmd_validate,
    _list_profiles,
    _print_collected,
    _run_profile,
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
    """_cmd_clean handles corrupted manifest JSON."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    ctx = tmp_path / "arachna_context"
    ctx.mkdir()
    (ctx / ".arachna_manifest.json").write_text("not json")

    _cmd_clean({}, ctx)


def test_cmd_clean_manifest_os_error(tmp_path, monkeypatch):
    """_cmd_clean handles OSError reading manifest."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    ctx = tmp_path / "arachna_context"
    ctx.mkdir()
    (ctx / ".arachna_manifest.json").write_text('{"files": ["chat-c.md"]}')

    with patch("pathlib.Path.read_text", side_effect=OSError("disk error")):
        _cmd_clean({}, ctx)


def test_cmd_validate_multiple_profiles(tmp_path, monkeypatch):
    """_cmd_validate with multiple profiles — one valid, one invalid."""
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
        _cmd_validate(config)
        mock_exit.assert_called_with(1)


def test_run_profile_invalid_name(tmp_path, monkeypatch):
    """_run_profile with invalid profile name exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )

    with pytest.raises(SystemExit):
        _run_profile(
            "nonexistent",
            json.loads((tmp_path / ".arachna.json").read_text()),
            Namespace(
                compress=False,
                format=None,
                dry_run=False,
                merge=False,
                verbose=False,
                incremental=False,
                all=False,
            ),
            "Test",
            tmp_path / "out",
        )


def test_run_profile_merge_no_clean(tmp_path, monkeypatch):
    """_run_profile with merge=True skips clean_manifest."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}})
    )

    config = json.loads((tmp_path / ".arachna.json").read_text())
    args = Namespace(
        compress=False,
        format=None,
        dry_run=False,
        merge=True,
        verbose=False,
        incremental=False,
        all=False,
    )

    created, _ = _run_profile("c", config, args, "Test", tmp_path / "out")
    assert len(created) == 1


def test_run_profile_dry_run(tmp_path, monkeypatch):
    """_run_profile with dry_run=True returns stats, not files."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}})
    )

    config = json.loads((tmp_path / ".arachna.json").read_text())
    args = Namespace(
        compress=False,
        format=None,
        dry_run=True,
        merge=False,
        verbose=False,
        incremental=False,
        all=False,
    )

    stats, tokens = _run_profile("c", config, args, "Test", tmp_path / "out")
    assert stats["name"] == "c"
    assert tokens == {}


def test_cmd_single_no_content(tmp_path, monkeypatch):
    """_cmd_single with empty profile prints 'No content collected'."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"e": {"directories": ["empty_dir"], "max_tokens": 100}}})
    )
    (tmp_path / "empty_dir").mkdir()

    config = json.loads((tmp_path / ".arachna.json").read_text())
    args = Namespace(
        profile="e",
        compress=False,
        format=None,
        dry_run=False,
        merge=False,
        verbose=False,
        incremental=False,
        all=False,
    )

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_single(config, args, "Test", tmp_path / "out")
    sys.stdout = old

    assert "No content collected" in out.getvalue()


def test_cmd_dry_run_with_args(tmp_path, monkeypatch):
    """_cmd_dry_run with --all shows multiple profiles."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "a": {"command": "echo hi", "max_tokens": 100},
                    "b": {"command": "echo bye", "max_tokens": 100},
                }
            }
        )
    )
    config = json.loads((tmp_path / ".arachna.json").read_text())
    args = Namespace(
        all=True,
        profile=None,
        compress=False,
        format=None,
        dry_run=True,
        merge=False,
        verbose=False,
        incremental=False,
    )

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_dry_run(config, args)
    sys.stdout = old

    output = out.getvalue()
    assert "[a] section" in output
    assert "[b] section" in output


def test_cmd_list_keyerror(tmp_path, monkeypatch):
    """_cmd_list handles KeyError from get_profile."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {"c": {"max_tokens": 100}}}))
    config = json.loads((tmp_path / ".arachna.json").read_text())

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_list(config)
    sys.stdout = old
