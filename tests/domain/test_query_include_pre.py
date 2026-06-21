"""Test _filter_by_query with include_pre_commands parameter."""

from arachna.domain.collection.gatherer_query import _filter_by_query
from arachna.domain.tokenization.tokenizer import count_tokens


def _make_section(filepath: str, content: str) -> tuple[str, str, int]:
    return (filepath, content, count_tokens(content))


def test_filter_by_query_include_pre_commands_true():
    sections = [
        _make_section("pre: tree src", "tree output"),
        _make_section("src/auth.py", "def login(): pass"),
        _make_section("src/utils.py", "def helper(): pass"),
    ]
    result = _filter_by_query(sections, "auth", include_pre_commands=True)
    paths = [r[0] for r in result]
    assert "pre: tree src" in paths
    assert "src/auth.py" in paths


def test_filter_by_query_include_pre_commands_false():
    sections = [
        _make_section("pre: tree src", "tree output"),
        _make_section("src/auth.py", "def login(): pass"),
    ]
    result = _filter_by_query(sections, "auth", include_pre_commands=False)
    paths = [r[0] for r in result]
    assert "pre: tree src" not in paths
    assert "src/auth.py" in paths


def test_filter_by_query_only_pre_commands_match():
    sections = [
        _make_section("pre: git log", "commit history"),
        _make_section("src/main.py", "unrelated"),
    ]
    result = _filter_by_query(sections, "git", include_pre_commands=True)
    paths = [r[0] for r in result]
    assert "pre: git log" in paths
    assert "src/main.py" not in paths
