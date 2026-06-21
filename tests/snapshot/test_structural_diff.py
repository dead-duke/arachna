"""Tests for structural diff in differ_structural.py."""

from arachna.domain.api_types import DiffSection
from arachna.domain.tokenization.language_dispatch import _parse_python_blocks
from arachna.snapshot.diff.differ_structural import (
    _extract_old_new_from_section,
    structural_diff,
    structural_diff_sections,
)


def test_parse_python_blocks():
    text = (
        "import os\n\ndef foo():\n    return 1\n\nclass Bar:\n    def method(self):\n        pass\n"
    )
    blocks = _parse_python_blocks(text)
    assert blocks is not None
    assert "foo" in blocks
    assert "Bar" in blocks
    sig, body = blocks["foo"]
    assert "def foo():" in sig
    assert "return 1" in body


def test_parse_python_blocks_empty():
    blocks = _parse_python_blocks("")
    assert blocks == {}


def test_parse_python_blocks_syntax_error():
    blocks = _parse_python_blocks("def foo(:\n    pass\n")
    assert blocks is None


def test_structural_diff_python_modified():
    old = "def foo():\n    return 1\n"
    new = "def foo():\n    return 2\n"
    result = structural_diff(old, new, "src/main.py", "python")
    assert "MODIFIED" in result
    assert "foo" in result


def test_structural_diff_python_added():
    old = "def foo():\n    return 1\n"
    new = "def foo():\n    return 1\n\ndef bar():\n    return 2\n"
    result = structural_diff(old, new, "src/main.py", "python")
    assert "ADDED" in result
    assert "bar" in result


def test_structural_diff_python_deleted():
    old = "def foo():\n    return 1\n\ndef bar():\n    return 2\n"
    new = "def foo():\n    return 1\n"
    result = structural_diff(old, new, "src/main.py", "python")
    assert "DELETED" in result
    assert "bar" in result


def test_structural_diff_python_signature_changed():
    old = "def foo(x):\n    return x\n"
    new = "def foo(x, y=0):\n    return x + y\n"
    result = structural_diff(old, new, "src/main.py", "python")
    assert "Signature changed" in result


def test_structural_diff_unknown_language_fallback():
    old = "line1\nline2\nline3\n"
    new = "line1\nchanged\nline3\n"
    result = structural_diff(old, new, "data.txt", "")
    assert "REMOVED" in result or "ADDED" in result


def test_extract_old_new_from_section():
    content = "### src/main.py\n\nREMOVED lines 1:\n    old line\n\nADDED lines 1:\n    new line\n"
    old, new = _extract_old_new_from_section(content)
    assert old.strip() == "old line"
    assert new.strip() == "new line"


def test_extract_old_new_from_section_empty():
    old, new = _extract_old_new_from_section("### src/main.py\n\n")
    assert old is None
    assert new is None


def test_structural_diff_sections_integration():
    sections = [
        DiffSection(
            type="modified",
            path="src/main.py",
            content="### src/main.py\n\nREMOVED lines 1-2:\n    def foo():\n        return 1\n\nADDED lines 1-2:\n    def foo():\n        return 2\n",
        ),
    ]
    result = structural_diff_sections(sections)
    assert len(result) == 1
    assert "MODIFIED" in result[0].content or "foo" in result[0].content
