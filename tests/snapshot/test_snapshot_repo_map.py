import pytest

from arachna.api.api_errors import SnapshotNotFoundError
from arachna.api.snapshot import compute_diff, create_snapshot
from arachna.config.core.config import get_profile, load_config
from arachna.config.profile_config import ProfileConfig
from arachna.domain.api_types import DiffSection
from arachna.domain.tokenization.language_dispatch import get_block_parser
from arachna.snapshot.snapshots import (
    _format_repo_map_added,
    _format_repo_map_diff,
    _read_file_from_disk,
    _read_file_from_store,
    apply_repo_map_to_sections,
)


def _resolve(tmp_path, profile):
    if isinstance(profile, ProfileConfig):
        return profile, load_config(root=tmp_path)
    config = load_config(root=tmp_path)
    return get_profile(profile, root=tmp_path, config=config), config


def test_format_repo_map_diff_sig_changed():
    old_blocks = {"foo": ("def foo(x):", "    return x")}
    new_blocks = {"foo": ("def foo(x, y=0):", "    return x")}
    result = _format_repo_map_diff("src/main.py", old_blocks, new_blocks)
    assert "~" in result
    assert "->" in result


def test_format_repo_map_diff_body_changed():
    old_blocks = {"foo": ("def foo():", "    return 1")}
    new_blocks = {"foo": ("def foo():", "    return 2")}
    result = _format_repo_map_diff("src/main.py", old_blocks, new_blocks)
    assert "body changed" in result


def test_format_repo_map_diff_added_block():
    old_blocks = {}
    new_blocks = {"bar": ("def bar():", "    pass")}
    result = _format_repo_map_diff("src/main.py", old_blocks, new_blocks)
    assert "+" in result
    assert "bar" in result


def test_format_repo_map_diff_deleted_block():
    old_blocks = {"foo": ("def foo():", "    return 1")}
    new_blocks = {}
    result = _format_repo_map_diff("src/main.py", old_blocks, new_blocks)
    assert "-" in result
    assert "foo" in result


def test_format_repo_map_diff_empty():
    result = _format_repo_map_diff("src/main.py", {}, {})
    assert result == ""


def test_format_repo_map_added_with_blocks():
    blocks = {"foo": ("def foo():", "    pass"), "bar": ("def bar():", "    pass")}
    result = _format_repo_map_added("src/new.py", blocks)
    assert "+ def foo():" in result
    assert "+ def bar():" in result


def test_format_repo_map_added_empty():
    result = _format_repo_map_added("src/new.py", {})
    assert result == ""


def test_get_block_parser_unknown_language():
    parser = get_block_parser("unknown_lang")
    assert parser is None


def test_get_block_parser_go():
    parser = get_block_parser("go")
    assert parser is not None
    text = "package main\n\nfunc main() {\n    return\n}\n"
    blocks = parser(text, "go")
    assert "main" in blocks


def test_get_block_parser_ruby():
    parser = get_block_parser("ruby")
    assert parser is not None
    text = "def hello\n    puts 'hi'\nend\n"
    blocks = parser(text)
    assert "hello" in blocks


def test_apply_repo_map_to_sections_modified(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="rm-mod")
    (src / "main.py").write_text("def foo():\n    return 2\n")
    sections = [
        DiffSection(
            type="modified",
            path="src/main.py",
            content="### src/main.py\n\nREMOVED lines 1:\n    old\n\nADDED lines 1:\n    new\n",
        )
    ]
    result = apply_repo_map_to_sections(sections, "rm-mod", None, root=root)
    assert len(result) == 1
    assert "foo" in result[0].content


def test_apply_repo_map_to_sections_added(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="rm-add")
    sections = [
        DiffSection(
            type="added",
            path="src/new.py",
            content="ADDED (new file):\n\n```\ndef new_func():\n    pass\n```\n",
        )
    ]
    result = apply_repo_map_to_sections(sections, "rm-add", None, root=root)
    assert len(result) == 1
    assert "new.py" in result[0].path or "new_func" in result[0].content


def test_apply_repo_map_to_sections_header_passthrough(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="rm-header")
    sections = [DiffSection(type="header", path="", content="## Changes\n")]
    result = apply_repo_map_to_sections(sections, "rm-header", None, root=root)
    assert result[0].type == "header"
    assert result[0].content == "## Changes\n"


def test_apply_repo_map_to_sections_deleted(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="rm-del")
    sections = [DiffSection(type="deleted", path="src/main.py", content="[DELETED]\n")]
    result = apply_repo_map_to_sections(sections, "rm-del", None, root=root)
    assert len(result) == 1
    assert "Removed signatures" in result[0].content or "DELETED" in result[0].content


def test_apply_repo_map_to_sections_cannot_read(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="rm-readfail")
    sections = [
        DiffSection(
            type="modified",
            path="nonexistent.py",
            content="### nonexistent.py\n\nREMOVED lines 1:\n    old\n",
        )
    ]
    result = apply_repo_map_to_sections(sections, "rm-readfail", None, root=root)
    assert len(result) == 1
    assert "REMOVED" in result[0].content


def test_compute_diff_snapshot_not_found(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    with pytest.raises(SnapshotNotFoundError):
        compute_diff(root=root, profile=profile, config=config)


def test_read_file_from_store_not_found(tmp_path):
    result = _read_file_from_store("nonexistent.py", {"other.py": "sha256:abc123"}, root=tmp_path)
    assert result is None


def test_read_file_from_store_invalid_hash(tmp_path):
    result = _read_file_from_store("test.py", {"test.py": "sha256:invalidhash"}, root=tmp_path)
    assert result is None


def test_read_file_from_disk_not_found(tmp_path):
    result = _read_file_from_disk(str(tmp_path / "ghost.py"))
    assert result is None


def test_read_file_from_disk_not_a_file(tmp_path):
    result = _read_file_from_disk(str(tmp_path))
    assert result is None


def test_read_file_from_disk_unreadable(tmp_path):
    import sys

    if sys.platform == "win32":
        pytest.skip("chmod 0o000 does not work on Windows")
    f = tmp_path / "secret.py"
    f.write_text("secret")
    f.chmod(0o000)
    try:
        result = _read_file_from_disk(str(f))
        assert result is None
    finally:
        f.chmod(0o644)
