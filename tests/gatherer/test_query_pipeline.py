"""Tests for decomposed query pipeline: _score_files, _build_reverse_graph, _expand_import_chain."""

from arachna.domain.gatherer import (
    _build_reverse_graph,
    _expand_import_chain,
    _score_files,
)
from arachna.domain.tokenizer import count_tokens


def _make_section(filepath: str, content: str) -> tuple[str, str, int]:
    return (filepath, content, count_tokens(content))


def test_score_files_filename_match():
    sections = [
        _make_section("src/auth.py", "x = 1"),
        _make_section("src/utils.py", "y = 2"),
    ]
    scores = _score_files(sections, ["auth"], {})
    assert "src/auth.py" in scores
    assert scores["src/auth.py"] >= 10


def test_score_files_content_match():
    sections = [
        _make_section("src/main.py", "authentication middleware here"),
        _make_section("src/utils.py", "unrelated stuff"),
    ]
    scores = _score_files(sections, ["authentication"], {})
    assert "src/main.py" in scores
    assert scores["src/main.py"] >= 3


def test_score_files_no_match():
    sections = [
        _make_section("src/main.py", "print('hello')"),
    ]
    scores = _score_files(sections, ["nonexistent"], {})
    assert scores == {}


def test_score_files_skips_pre_commands():
    sections = [
        _make_section("pre: tree src", "tree output"),
        _make_section("src/auth.py", "def login(): pass"),
    ]
    scores = _score_files(sections, ["tree"], {})
    assert "pre: tree src" not in scores


def test_build_reverse_graph():
    graph = {
        "src/auth.py": ["crypto", "db"],
        "src/crypto.py": ["hashlib"],
        "src/main.py": ["auth"],
    }
    reverse = _build_reverse_graph(graph)
    assert "auth" in reverse
    assert "src/main.py" in reverse["auth"]
    assert "crypto" in reverse
    assert "src/auth.py" in reverse["crypto"]


def test_expand_import_chain():
    reverse_graph = {
        "auth": ["src/main.py", "src/api.py"],
        "main": ["src/app.py"],
    }
    matched = {"src/auth.py"}
    expanded = _expand_import_chain(matched, reverse_graph, depth=2)
    assert "src/main.py" in expanded
    assert "src/api.py" in expanded


def test_expand_import_chain_no_expansion():
    reverse_graph = {}
    matched = {"src/auth.py"}
    expanded = _expand_import_chain(matched, reverse_graph)
    assert expanded == matched
