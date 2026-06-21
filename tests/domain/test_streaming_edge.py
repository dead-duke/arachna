from pathlib import Path

from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.gatherer import _assemble_content, _assemble_file_content
from arachna.domain.collection.gatherer_query import _filter_filenames_by_query
from arachna.domain.tokenization.tokenizer import count_tokens


def _file_profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def _cmd_profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_file",
        command="echo 'cmd output'",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_stream_full_mode_pre_commands_only(tmp_path):
    src = tmp_path / "src"
    src.mkdir()

    p = _file_profile(pre_commands=["echo 'section1'", "echo 'section2'"])

    named, parts, indices, cache = _assemble_file_content(
        p,
        [],
        count_tokens,
        root=tmp_path,
    )

    assert len(parts) >= 1
    assert any("section1" in part for part in parts)
    assert any("section2" in part for part in parts)


def test_stream_full_mode_pre_commands_exceed_limit(tmp_path):
    src = tmp_path / "src"
    src.mkdir()

    p = _file_profile(pre_commands=["echo '" + "x" * 2000 + "'"], max_tokens=10)

    named, parts, indices, cache = _assemble_file_content(
        p,
        [],
        count_tokens,
        root=tmp_path,
    )

    assert len(parts) >= 1


def test_stream_full_mode_with_compress(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("a\n\n\n\nb\n")

    p = _file_profile(compress=True)

    named, parts, indices, cache = _assemble_file_content(
        p,
        [],
        count_tokens,
        root=tmp_path,
    )

    assert len(parts) == 1
    assert "\n\n\n\n" not in parts[0]


def test_stream_full_mode_verbose_compress_stats(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("a\n\n\n\nb\n")

    p = _file_profile(compress=True)

    _assemble_content(p, [], count_tokens, verbose=True, root=tmp_path)

    captured = capsys.readouterr()
    assert "Compressed:" in captured.out


def test_assemble_content_command_wins(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")

    p = _cmd_profile()

    named, parts, indices, cache = _assemble_content(p, [], count_tokens, root=tmp_path)

    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "command" in captured.out.lower()


def test_filter_filenames_by_query_empty():
    files = [Path("src/main.py"), Path("src/utils.py")]
    result = _filter_filenames_by_query(files, "")
    assert len(result) == 2


def test_filter_filenames_by_query_whitespace():
    files = [Path("src/main.py")]
    result = _filter_filenames_by_query(files, "   ")
    assert len(result) == 1


def test_filter_filenames_by_query_match():
    files = [Path("src/auth.py"), Path("src/utils.py")]
    result = _filter_filenames_by_query(files, "auth")
    assert len(result) == 1
    assert result[0].name == "auth.py"


def test_filter_filenames_by_query_no_match():
    files = [Path("src/main.py")]
    result = _filter_filenames_by_query(files, "nonexistent")
    assert len(result) == 0


def test_filter_filenames_by_query_case_insensitive():
    files = [Path("src/Auth.py")]
    result = _filter_filenames_by_query(files, "auth")
    assert len(result) == 1
