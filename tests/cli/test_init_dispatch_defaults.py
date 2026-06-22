"""Tests for init dispatch — defaults path."""

from argparse import Namespace

from arachna.cli.init import _dispatch_init
from arachna.config.profile_config import ArachnaConfig


def test_dispatch_init_defaults_creates_config(tmp_path):
    """_dispatch_init without install_hook calls _cmd_init with defaults."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    (tmp_path / ".git").mkdir()
    config = ArachnaConfig(project_name="test", output_dir="out", _root=str(tmp_path), profiles={})
    args = Namespace(defaults=True, preset=None, install_hook=False, output_dir=None, force=False)
    _dispatch_init(args, config)
    assert (tmp_path / ".arachna.json").exists()
