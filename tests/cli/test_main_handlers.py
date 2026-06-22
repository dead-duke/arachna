"""Coverage for __main__.py uncovered branches."""

import json
from io import StringIO
from unittest.mock import patch

from arachna.cli._helpers import list_profiles, print_collected, write_manifest
from arachna.cli.collect import _cmd_collect_clean, _cmd_collect_list, _cmd_collect_validate
from arachna.config.core.config import load_config
from arachna.domain.path_utils import SafePath


def test_list_profiles_empty_config():
    assert list_profiles({"profiles": {}}) == ["default"]


def test_list_profiles_no_key():
    assert list_profiles({}) == ["default"]


def test_print_collected_empty():
    import sys

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    print_collected([])
    sys.stdout = old
    assert "No content collected" in out.getvalue()


def test_print_collected_with_files(tmp_path):
    import sys

    f = tmp_path / "chat-c.md"
    f.write_text("hello world")
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    print_collected([str(f)])
    sys.stdout = old
    assert "chat-c.md" in out.getvalue()


def test_write_manifest(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    f1 = str(out / "chat-c.md")
    (out / "chat-c.md").write_text("content")
    write_manifest(SafePath(out, tmp_path), [f1], {f1: 10}, {"project_name": "Test"})
    mf = out / "chat-manifest.md"
    assert mf.exists()
    content = mf.read_text()
    assert "Test" in content
    assert "chat-c.md" in content


def test_cmd_clean_corrupted_manifest(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": str(tmp_path / "out"),
                "profiles": {"c": {"directories": ["src"], "max_tokens": 100}},
            }
        )
    )
    config = load_config(root=tmp_path)
    config._root = str(tmp_path)
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / ".arachna_manifest.json").write_text("not json")
    from argparse import Namespace

    _cmd_collect_clean(Namespace(output_dir=None), config)


def test_cmd_clean_manifest_os_error(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": str(tmp_path / "out"),
                "profiles": {"c": {"directories": ["src"], "max_tokens": 100}},
            }
        )
    )
    config = load_config(root=tmp_path)
    config._root = str(tmp_path)
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / ".arachna_manifest.json").write_text('{"files": ["chat-c.md"]}')
    from argparse import Namespace

    with patch("pathlib.Path.read_text", side_effect=OSError("disk error")):
        _cmd_collect_clean(Namespace(output_dir=None), config)


def test_cmd_validate_multiple_profiles(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": str(tmp_path / "out"),
                "profiles": {
                    "good": {"directories": ["src"], "max_tokens": 100},
                    "bad": {"max_tokens": 0},
                },
            }
        )
    )
    config = load_config(root=tmp_path)
    config._root = str(tmp_path)
    from argparse import Namespace

    with patch("sys.exit") as mock_exit:
        _cmd_collect_validate(Namespace(), config)
        mock_exit.assert_called_with(1)


def test_cmd_list_keyerror(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": str(tmp_path / "out"),
                "profiles": {"c": {"max_tokens": 100}},
            }
        )
    )
    config = load_config(root=tmp_path)
    config._root = str(tmp_path)
    import sys
    from argparse import Namespace

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_collect_list(Namespace(), config)
    sys.stdout = old
