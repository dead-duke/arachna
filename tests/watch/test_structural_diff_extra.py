"""Extra coverage for differ_structural.py — C-like, script, fallback, formatting."""

from arachna.domain.language_dispatch import (
    _extract_braced_block,
    _parse_c_like_blocks,
    _parse_script_blocks,
)
from arachna.watch.differ_structural import (
    _block_label,
    _fallback_diff,
    _format_block_diff,
    structural_diff,
)


def test_parse_c_like_blocks_javascript():
    text = (
        "import React from 'react';\n\n"
        "export function App() {\n    return <div>Hello</div>;\n}\n\n"
        "export class Component {\n    render() {\n        return null;\n    }\n}\n"
    )
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
    assert "function foo" in _block_label("foo", "def foo(x):")
    assert "function main" in _block_label("main", "func main() {")


def test_block_label_class():
    assert "class MyClass" in _block_label("MyClass", "class MyClass:")


def test_block_label_unknown():
    assert _block_label("x", "something else") == "x"


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
