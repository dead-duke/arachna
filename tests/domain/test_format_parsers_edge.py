"""Edge case tests for format_parsers.py — uncovered branches."""

from arachna.domain.formatting.format_parsers import (
    _parse_import_stmt,
    _parse_multiline_import,
    _parse_python_import,
)


def test_parse_python_import_normal():
    """Standard import line returns list of modules."""
    result = _parse_python_import("import os, sys, json")
    assert result == ["os", "sys", "json"]


def test_parse_python_import_single():
    """Single module import."""
    result = _parse_python_import("import os")
    assert result == ["os"]


def test_parse_python_import_empty_modules():
    """import with no module name returns empty list."""
    result = _parse_python_import("import ")
    assert result == []


def test_parse_python_import_whitespace_only():
    """import followed by whitespace only returns empty list."""
    result = _parse_python_import("import   ")
    assert result == []


def test_parse_python_import_not_import():
    """Non-import line returns empty list."""
    result = _parse_python_import("from os import path")
    assert result == []


def test_parse_python_import_with_spaces():
    """Modules with extra spaces are stripped correctly."""
    result = _parse_python_import("import  os,  sys , json ")
    assert result == ["os", "sys", "json"]


def test_parse_import_stmt_two_groups():
    """Match with two groups returns all parts."""
    import re

    pattern = re.compile(r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]")
    match = pattern.search("import foo from 'bar'")
    result = _parse_import_stmt(match)
    assert "foo" in result
    assert "bar" in result


def test_parse_import_stmt_group1_with_commas():
    """First group split by commas produces multiple deps."""
    import re

    pattern = re.compile(r"import\s+\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]")
    match = pattern.search("import { foo, bar, baz } from 'module'")
    result = _parse_import_stmt(match)
    assert "foo" in result
    assert "bar" in result
    assert "baz" in result
    assert "module" in result


def test_parse_import_stmt_empty_groups():
    """Match with empty groups returns empty list."""
    import re

    pattern = re.compile(r"import\s+(\w*)\s+from\s+['\"]([^'\"]*)['\"]")
    match = pattern.search("import  from ''")
    result = _parse_import_stmt(match)
    assert result == []


def test_parse_multiline_import_simple():
    """Multiline import with multiple modules."""
    import re

    pattern = re.compile(r"import\s*\(([^)]*)\)", re.MULTILINE)
    match = pattern.search("import (\n    os,\n    sys,\n    json\n)")
    result = _parse_multiline_import(match)
    assert "os" in result
    assert "sys" in result
    assert "json" in result


def test_parse_multiline_import_single():
    """Multiline import with single module."""
    import re

    pattern = re.compile(r"import\s*\(([^)]*)\)", re.MULTILINE)
    match = pattern.search("import (os)")
    result = _parse_multiline_import(match)
    assert result == ["os"]


def test_parse_multiline_import_empty():
    """Multiline import with empty parens."""
    import re

    pattern = re.compile(r"import\s*\(([^)]*)\)", re.MULTILINE)
    match = pattern.search("import ()")
    result = _parse_multiline_import(match)
    assert result == []
