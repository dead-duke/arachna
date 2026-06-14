"""Coverage for streaming pipeline edge cases in gatherer.py."""

from arachna.gatherer import _assemble_content, _assemble_file_content, _filter_filenames_by_query
from arachna.tokenizer import count_tokens


def test_stream_full_mode_pre_commands_only(tmp_path):
    src = tmp_path / "src"
    src.mkdir()

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": ["echo 'section1'", "echo 'section2'"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "use_gitignore": False,
    }

    named, parts, indices, cache = _assemble_file_content(
        profile,
        [],
        count_tokens,
        root=tmp_path,
    )

    assert len(parts) >= 1
    assert any("section1" in p for p in parts)
    assert any("section2" in p for p in parts)


def test_stream_full_mode_pre_commands_exceed_limit(tmp_path):
    src = tmp_path / "src"
    src.mkdir()

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": ["echo '" + "x" * 2000 + "'"],
        "max_tokens": 10,
        "split_mode": "by_file",
        "use_gitignore": False,
    }

    named, parts, indices, cache = _assemble_file_content(
        profile,
        [],
        count_tokens,
        root=tmp_path,
    )

    assert len(parts) >= 1


def test_stream_full_mode_with_compress(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("a\n\n\n\nb\n")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": [],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "compress": True,
        "use_gitignore": False,
    }

    named, parts, indices, cache = _assemble_file_content(
        profile,
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

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": [],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "compress": True,
        "use_gitignore": False,
    }

    _assemble_content(profile, [], count_tokens, verbose=True, root=tmp_path)

    captured = capsys.readouterr()
    assert "Compressed:" in captured.out


def test_assemble_content_command_wins(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")

    profile = {
        "command": "echo 'cmd output'",
        "directories": ["src"],
        "patterns": ["*.py"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "use_gitignore": False,
    }

    named, parts, indices, cache = _assemble_content(profile, [], count_tokens, root=tmp_path)

    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "command" in captured.out.lower()


def test_filter_filenames_by_query_empty():
    from pathlib import Path

    files = [Path("src/main.py"), Path("src/utils.py")]
    result = _filter_filenames_by_query(files, "")
    assert len(result) == 2


def test_filter_filenames_by_query_whitespace():
    from pathlib import Path

    files = [Path("src/main.py")]
    result = _filter_filenames_by_query(files, "   ")
    assert len(result) == 1


def test_filter_filenames_by_query_match():
    from pathlib import Path

    files = [Path("src/auth.py"), Path("src/utils.py")]
    result = _filter_filenames_by_query(files, "auth")
    assert len(result) == 1
    assert result[0].name == "auth.py"


def test_filter_filenames_by_query_no_match():
    from pathlib import Path

    files = [Path("src/main.py")]
    result = _filter_filenames_by_query(files, "nonexistent")
    assert len(result) == 0


def test_filter_filenames_by_query_case_insensitive():
    from pathlib import Path

    files = [Path("src/Auth.py")]
    result = _filter_filenames_by_query(files, "auth")
    assert len(result) == 1
