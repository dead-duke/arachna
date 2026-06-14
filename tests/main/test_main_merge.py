from arachna.cli.collect import _cmd_collect_all, _cmd_collect_clean, _cmd_collect_profile


def _args(all=False, merge=False):
    from argparse import Namespace

    return Namespace(
        profile="code",
        all=all,
        dry_run=False,
        merge=merge,
        verbose=False,
        incremental=False,
        compress=False,
        format=None,
        query=None,
        mode="full",
        no_pre_commands=False,
        output_dir=None,
    )


def _clean_args():
    from argparse import Namespace

    return Namespace(output_dir=None)


def test_merge_then_clean_removes_all(tmp_path, make_config):
    config = make_config(
        tmp_path,
        profiles={
            "code": {
                "directories": ["src"],
                "max_tokens": 10,
                "patterns": ["*.py"],
                "split_mode": "by_file",
                "use_gitignore": False,
            }
        },
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x" * 200)
    (tmp_path / "src" / "b.py").write_text("y" * 200)

    _cmd_collect_profile(_args(merge=True), config)
    files1 = sorted((tmp_path / "out").glob("chat-code*.md"))
    assert len(files1) >= 2

    _cmd_collect_profile(_args(merge=True), config)
    files2 = sorted((tmp_path / "out").glob("chat-code*.md"))
    assert len(files2) >= 4

    _cmd_collect_clean(_clean_args(), config)
    files3 = list((tmp_path / "out").glob("chat-code*.md"))
    assert len(files3) == 0


def test_merge_then_all_cleans_globally(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("print('hi')")

    _cmd_collect_profile(_args(merge=True), config)
    files1 = sorted((tmp_path / "out").glob("chat-code*.md"))
    assert len(files1) == 1

    _cmd_collect_all(_args(all=True), config)
    files2 = sorted((tmp_path / "out").glob("chat-code*.md"))
    assert len(files2) == 1


def test_merge_single_part_sequential(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("print('hi')")

    for _ in range(3):
        _cmd_collect_profile(_args(merge=True), config)

    files = sorted((tmp_path / "out").glob("chat-code*.md"))
    assert len(files) == 3
    names = [f.name for f in files]
    assert "chat-code_1.md" in names
    assert "chat-code_2.md" in names
    assert "chat-code_3.md" in names


def test_merge_single_profile_cli(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("print('hi')")

    _cmd_collect_profile(_args(merge=True), config)
    files1 = sorted((tmp_path / "out").glob("chat-code*.md"))
    assert len(files1) == 1
    assert "chat-code_1.md" in str(files1[0])

    _cmd_collect_profile(_args(merge=True), config)
    files2 = sorted((tmp_path / "out").glob("chat-code*.md"))
    assert len(files2) == 2
    assert "chat-code_2.md" in str(files2[1])
