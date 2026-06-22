"""Tests for structural diff — Python, JS, C-like, Ruby, fallback, block formatting."""

from arachna.domain.api_types import DiffSection
from arachna.domain.tokenization.language_dispatch import (
    _extract_braced_block,
    _parse_c_like_blocks,
    _parse_python_blocks,
    _parse_script_blocks,
)
from arachna.snapshot.diff.differ_structural import (
    _build_block_label,
    _extract_old_new_from_section,
    _fallback_diff,
    _format_block_diff,
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


# Extra coverage — C-like, script, fallback, formatting


def test_parse_c_like_blocks_javascript():
    text = "import React from 'react';\n\nexport function App() {\n    return <div>Hello</div>;\n}\n\nexport class Component {\n    render() {\n        return null;\n    }\n}\n"
    blocks = _parse_c_like_blocks(text, "javascript")
    assert "App" in blocks
    assert "Component" in blocks


def test_parse_c_like_blocks_go():
    text = 'package main\n\nfunc main() {\n    fmt.Println("hello")\n}\n\nfunc Handler() {\n    return\n}\n'
    blocks = _parse_c_like_blocks(text, "go")
    assert "main" in blocks
    assert "Handler" in blocks


def test_parse_c_like_blocks_go_type_struct():
    text = "package main\n\ntype Handler struct {\n    db *sql.DB\n}\n\ntype Server interface {\n    Start() error\n}\n"
    blocks = _parse_c_like_blocks(text, "go")
    assert "Handler" in blocks
    assert "Server" in blocks


def test_parse_script_blocks_ruby():
    text = "def initialize(name)\n    @name = name\nend\n\ndef self.from_json(data)\n    new(data['name'])\nend\n"
    blocks = _parse_script_blocks(text)
    assert "initialize" in blocks
    assert "from_json" in blocks


def test_extract_braced_block_simple():
    assert _extract_braced_block("{ hello world } extra", 0) == "{ hello world }"


def test_extract_braced_block_nested():
    assert (
        _extract_braced_block("{ outer { inner } still outer } after", 0)
        == "{ outer { inner } still outer }"
    )


def test_extract_braced_block_no_brace():
    assert _extract_braced_block("no brace", 0) == ""


def test_extract_braced_block_past_end():
    assert _extract_braced_block("hi", 10) == ""


def test_block_label_function():
    assert "function foo" in _build_block_label("foo", "def foo(x):")
    assert "function main" in _build_block_label("main", "func main() {")


def test_block_label_class():
    assert "class MyClass" in _build_block_label("MyClass", "class MyClass:")


def test_block_label_unknown():
    assert _build_block_label("x", "something else") == "x"


def test_format_block_diff_added():
    result = _format_block_diff(
        {}, {"foo": ("def foo():", "    return 1")}, "src/test.py", "markdown"
    )
    assert "ADDED" in result


def test_format_block_diff_deleted():
    result = _format_block_diff(
        {"foo": ("def foo():", "    return 1")}, {}, "src/test.py", "markdown"
    )
    assert "DELETED" in result


def test_format_block_diff_unchanged():
    result = _format_block_diff(
        {"foo": ("def foo():", "    return 1")},
        {"foo": ("def foo():", "    return 1")},
        "src/test.py",
        "markdown",
    )
    assert "MODIFIED" not in result


def test_format_block_diff_signature_changed():
    result = _format_block_diff(
        {"foo": ("def foo(x):", "    return x")},
        {"foo": ("def foo(x, y=0):", "    return x + y")},
        "src/test.py",
        "markdown",
    )
    assert "Signature changed" in result


def test_format_block_diff_body_changed():
    result = _format_block_diff(
        {"foo": ("def foo():", "    return 1")},
        {"foo": ("def foo():", "    return 2")},
        "src/test.py",
        "markdown",
    )
    assert "Body:" in result


def test_fallback_diff():
    result = _fallback_diff("old", "new", "test.txt", "markdown")
    assert "test.txt" in result


def test_structural_diff_javascript():
    old = "function foo() {\n    return 1;\n}\n"
    new = "function foo() {\n    return 2;\n}\n"
    result = structural_diff(old, new, "src/app.js", "javascript", "markdown")
    assert "src/app.js" in result
    assert len(result) > 0
    assert any(kw in result for kw in ["MODIFIED", "REMOVED", "ADDED"])


def test_structural_diff_ruby():
    old = "def foo\n    return 1\nend\n"
    new = "def foo\n    return 2\nend\n"
    result = structural_diff(old, new, "src/helper.rb", "ruby", "markdown")
    assert "MODIFIED" in result
