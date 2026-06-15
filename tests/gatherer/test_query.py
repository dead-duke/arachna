"""Tests for _filter_by_query and _collect_import_graph in gatherer.py."""

from arachna.domain.gatherer import _collect_import_graph, _filter_by_query
from arachna.domain.tokenizer import count_tokens


def _make_section(filepath: str, content: str) -> tuple[str, str, int]:
    return (filepath, content, count_tokens(content))


def _make_python_section(
    filepath: str, imports: str = "", funcs: str = "", body: str = ""
) -> tuple[str, str, int]:
    content = ""
    if imports:
        content += imports + "\n\n"
    if funcs:
        content += funcs + "\n\n"
    if body:
        content += body
    if not content:
        content = "x = 1\n"
    return _make_section(filepath, content)


def test_filter_by_query_empty_query():
    sections = [
        _make_section("src/main.py", "print('hello')"),
        _make_section("src/utils.py", "def foo(): pass"),
    ]
    result = _filter_by_query(sections, "")
    assert len(result) == 2

    result_none = _filter_by_query(sections, "   ")
    assert len(result_none) == 2


def test_filter_by_query_filename_match():
    sections = [
        _make_section("src/auth.py", "x = 1"),
        _make_section("src/utils.py", "y = 2"),
    ]
    result = _filter_by_query(sections, "auth")
    assert len(result) == 1
    assert result[0][0] == "src/auth.py"


def test_filter_by_query_content_match():
    sections = [
        _make_section("src/main.py", "authentication middleware here"),
        _make_section("src/utils.py", "unrelated stuff"),
    ]
    result = _filter_by_query(sections, "authentication")
    assert len(result) == 1
    assert "main.py" in result[0][0]


def test_filter_by_query_no_match():
    sections = [
        _make_section("src/main.py", "print('hello')"),
        _make_section("src/utils.py", "def foo(): pass"),
    ]
    result = _filter_by_query(sections, "nonexistent_xyz")
    assert len(result) == 0


def test_filter_by_query_multiple_words():
    sections = [
        _make_section("src/auth.py", "login handler"),
        _make_section("src/payment.py", "process payment"),
        _make_section("src/utils.py", "helper functions"),
    ]
    result = _filter_by_query(sections, "auth payment")
    assert len(result) == 2
    paths = [r[0] for r in result]
    assert "src/auth.py" in paths
    assert "src/payment.py" in paths


def test_collect_import_graph():
    sections = [
        _make_python_section(
            "src/auth.py", "import crypto\nfrom db import users", "def login(): pass"
        ),
        _make_python_section("src/crypto.py", "import hashlib", "def hash_pw(): pass"),
        _make_python_section("src/db/users.py", "import sqlite3", "def get_user(): pass"),
    ]
    graph_cache = {}
    graph = _collect_import_graph(sections, graph_cache)
    assert "src/auth.py" in graph
    assert "crypto" in graph["src/auth.py"]
    assert "db" in graph["src/auth.py"]


def test_filter_by_query_import_chain():
    sections = [
        _make_python_section("src/auth.py", "import crypto", "def login(): pass"),
        _make_python_section("src/crypto.py", "", "def hash_pw(): pass\ndef verify_pw(): pass"),
        _make_python_section("src/main.py", "import auth", "def main(): pass"),
    ]
    result = _filter_by_query(sections, "crypto")
    paths = [r[0] for r in result]
    assert "src/crypto.py" in paths
    assert "src/auth.py" in paths, f"auth.py not in results: {paths}"
    assert "src/main.py" in paths, f"main.py not in results: {paths}"


def test_query_preserves_order():
    sections = [
        _make_section("src/z.py", "x"),
        _make_section("src/a.py", "query"),
        _make_section("src/m.py", "x"),
        _make_section("src/b.py", "query"),
    ]
    result = _filter_by_query(sections, "query")
    assert len(result) == 2
    assert result[0][0] == "src/a.py"
    assert result[1][0] == "src/b.py"
