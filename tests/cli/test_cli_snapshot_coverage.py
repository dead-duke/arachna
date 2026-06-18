"""Coverage for Watch CLI handlers."""

from io import StringIO

from arachna.cli.diff import _cmd_diff
from arachna.cli.snapshot import _cmd_snapshot_create, _cmd_snapshot_info, _cmd_snapshot_update


def _snap_create(name, profile):
    from argparse import Namespace

    return Namespace(name=name, profile=profile)


def _snap_update(sid, profile=None):
    from argparse import Namespace

    return Namespace(id=sid, profile=profile)


def _snap_info(sid, profile_only=False, stats_only=False):
    from argparse import Namespace

    return Namespace(id=sid, profile_only=profile_only, stats_only=stats_only)


def _diff_args(
    fr=None,
    to=None,
    all=False,
    profile=None,
    stat=False,
    flat=False,
    fmt=None,
    mode=None,
    compress=False,
):
    from argparse import Namespace

    return Namespace(
        from_snapshot=fr,
        to=to,
        all=all,
        profile=profile,
        stat=stat,
        flat=flat,
        format=fmt,
        mode=mode,
        compress=compress,
        output_dir=None,
        query=None,
    )


def test_cmd_diff_format_xml(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("original")
    _cmd_snapshot_create(_snap_create("xml-test", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("modified for xml")
    _cmd_diff(_diff_args(fr="xml-test", profile="code", fmt="xml"), config)
    files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    # XML format is inside diff content after markdown header/TOC
    assert '<file path="' in content


def test_cmd_diff_mode_structural(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("def foo():\n    return 1\n")
    _cmd_snapshot_create(_snap_create("struct-cov", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("def foo():\n    return 2\n")
    _cmd_diff(_diff_args(fr="struct-cov", profile="code", mode="structural"), config)
    files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "MODIFIED" in content or "modified" in content.lower()


def test_cmd_diff_mode_repo_map(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text(
        "def foo():\n    return 1\n\ndef bar():\n    return 2\n"
    )
    _cmd_snapshot_create(_snap_create("rm-cov", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text(
        "def foo():\n    return 3\n\ndef bar():\n    return 4\n"
    )
    _cmd_diff(_diff_args(fr="rm-cov", profile="code", mode="repo-map"), config)
    files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content


def test_cmd_diff_compress(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("original\n\n\n\nspaces")
    _cmd_snapshot_create(_snap_create("comp-cov", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("modified\n\n\n\nafter")
    _cmd_diff(_diff_args(fr="comp-cov", profile="code", compress=True), config)
    files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(files) >= 1


def test_cmd_snapshot_info_full_output(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    config["profiles"]["code"]["pre_commands"] = ["echo hello"]
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("info-full", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_info(_snap_info("info-full"), config)
    sys.stdout = old
    output = out.getvalue()
    assert "Snapshot: info-full" in output
    assert "Created:" in output
    assert "Files:" in output
    assert "Pre-commands:" in output
    assert "Profile:" in output


def test_cmd_snapshot_update_with_profile(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("upd-cov", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_update(_snap_update("upd-cov", "code"), config)
    sys.stdout = old
    assert "updated" in out.getvalue()


def test_cmd_diff_stat_only_output(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("original")
    _cmd_snapshot_create(_snap_create("stat-cov", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("modified v2")
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_diff_args(fr="stat-cov", profile="code", stat=True), config)
    sys.stdout = old
    output = out.getvalue()
    assert "Modified:" in output
    assert "Added:" in output
    assert "Deleted:" in output
    assert "Tokens:" in output


def test_cmd_diff_flat_output(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("original")
    _cmd_snapshot_create(_snap_create("flat-cov", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("modified flat")
    _cmd_diff(_diff_args(fr="flat-cov", profile="code", flat=True), config)
    files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(files) >= 1
