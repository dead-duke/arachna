"""Coverage for pre_commands handling in gatherer.py."""

from arachna.gatherer import _assemble_content, _collect_pre_commands
from arachna.tokenizer import count_tokens


def test_collect_pre_commands_empty_list(tmp_path, monkeypatch):
    """Empty pre_commands returns empty list."""
    monkeypatch.chdir(tmp_path)
    result = _collect_pre_commands(
        {"pre_commands": []},
        count_tokens,
    )
    assert result == []


def test_collect_pre_commands_no_key(tmp_path, monkeypatch):
    """Profile without pre_commands key returns empty list."""
    monkeypatch.chdir(tmp_path)
    result = _collect_pre_commands(
        {"directories": ["src"], "max_tokens": 100},
        count_tokens,
    )
    assert result == []


def test_assemble_content_with_query(tmp_path, monkeypatch):
    """_assemble_content with query passes query through."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass")
    (src / "utils.py").write_text("def helper(): pass")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": [],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "use_gitignore": False,
    }

    named, parts, indices, cache = _assemble_content(
        profile,
        [],
        count_tokens,
        query="auth",
        mode="full",
    )

    assert len(named) == 1
    assert "auth.py" in named[0][0]


def test_assemble_content_streaming_with_query(tmp_path, monkeypatch):
    """Streaming mode with query filters files before reading."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "keep.py").write_text("important")
    (src / "skip.py").write_text("unrelated")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": [],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "use_gitignore": False,
    }

    named, parts, indices, cache = _assemble_content(
        profile,
        [],
        count_tokens,
        query="keep",
        mode="full",
    )

    assert len(parts) >= 1
    content = parts[0]
    assert "keep.py" in content
    assert "skip.py" not in content


def test_assemble_file_content_streaming_verbose_compress(tmp_path, monkeypatch, capsys):
    """Streaming mode with verbose and compress prints stats."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("a\n\n\n\nb\n")

    from arachna.gatherer import _assemble_file_content

    _assemble_file_content(
        {
            "directories": ["src"],
            "patterns": ["*.py"],
            "pre_commands": [],
            "max_tokens": 16000,
            "split_mode": "by_file",
            "compress": True,
            "use_gitignore": False,
        },
        [],
        count_tokens,
        incremental=False,
        cache=None,
        verbose=True,
    )

    captured = capsys.readouterr()
    assert "Compressed:" in captured.out
