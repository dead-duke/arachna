"""Tests for store CLI handlers — stats, gc."""

from io import StringIO

from arachna.cli.store import _cmd_store_gc, _cmd_store_stats


def _store_args():
    from argparse import Namespace

    return Namespace()


def test_cmd_store_stats_empty(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_store_stats(_store_args(), config)
    sys.stdout = old
    output = out.getvalue()
    assert "Snapshots: 0" in output
    assert "Objects: 0" in output


def test_cmd_store_gc_empty(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_store_gc(_store_args(), config)
    sys.stdout = old
    assert "No objects to collect" in out.getvalue()
