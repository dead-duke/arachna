"""Extra coverage for differ_structural.py — C-like, script, fallback, formatting."""

from arachna.differ_structural import (
    _block_label,
    _extract_braced_block,
    _fallback_diff,
    _format_block_diff,
    _parse_c_like_blocks,
    _parse_script_blocks,
    structural_diff,
)


def test_parse_c_like_blocks_javascript():
    """Parse JavaScript source into named blocks."""
    text = (
        "import React from 'react';\n"
        "\n"
        "export function App() {\n"
        "    return <div>Hello</div>;\n"
        "}\n"
        "\n"
        "export class Component {\n"
        "    render() {\n"
        "        return null;\n"
        "    }\n"
        "}\n"
    )
    blocks = _parse_c_like_blocks(text, "javascript")
    assert "App" in blocks
    assert "Component" in blocks
    sig, body = blocks["App"]
    assert "export function App()" in sig
    assert "return <div>Hello</div>" in body


def test_parse_c_like_blocks_go():
    """Parse Go source into named blocks."""
    text = (
        "package main\n\n"
        "func main() {\n"
        '    fmt.Println("hello")\n'
        "}\n"
        "\n"
        "func Handler() {\n"
        "    return\n"
        "}\n"
    )
    blocks = _parse_c_like_blocks(text, "go")
    assert "main" in blocks
    assert "Handler" in blocks


def test_parse_c_like_blocks_go_type_struct():
    """Go type struct — block name is the type name, not 'struct' (MEDIUM-15)."""
    text = (
        "package main\n\n"
        "type Handler struct {\n"
        "    db *sql.DB\n"
        "}\n"
        "\n"
        "type Server interface {\n"
        "    Start() error\n"
        "}\n"
    )
    blocks = _parse_c_like_blocks(text, "go")
    assert "Handler" in blocks, f"Expected 'Handler' in blocks, got {list(blocks.keys())}"
    assert "Server" in blocks, f"Expected 'Server' in blocks, got {list(blocks.keys())}"
    sig, body = blocks["Handler"]
    assert "type Handler struct" in sig
    assert "db *sql.DB" in body


def test_parse_script_blocks_ruby():
    """Parse Ruby source into named blocks."""
    text = (
        "def initialize(name)\n"
        "    @name = name\n"
        "end\n"
        "\n"
        "def self.from_json(data)\n"
        "    new(data['name'])\n"
        "end\n"
    )
    blocks = _parse_script_blocks(text)
    assert "initialize" in blocks
    assert "from_json" in blocks


def test_extract_braced_block_simple():
    """Extract a simple braced block."""
    text = "{ hello world } extra"
    result = _extract_braced_block(text, 0)
    assert result == "{ hello world }"


def test_extract_braced_block_nested():
    """Extract a nested braced block."""
    text = "{ outer { inner } still outer } after"
    result = _extract_braced_block(text, 0)
    assert result == "{ outer { inner } still outer }"


def test_extract_braced_block_no_brace():
    """No brace at start returns empty."""
    result = _extract_braced_block("no brace", 0)
    assert result == ""


def test_extract_braced_block_past_end():
    """Start past end returns empty."""
    result = _extract_braced_block("hi", 10)
    assert result == ""


def test_block_label_function():
    """_block_label identifies functions."""
    assert "function foo" in _block_label("foo", "def foo(x):")
    assert "function main" in _block_label("main", "func main() {")


def test_block_label_class():
    """_block_label identifies classes."""
    assert "class MyClass" in _block_label("MyClass", "class MyClass:")


def test_block_label_unknown():
    """_block_label falls back to just name."""
    assert _block_label("x", "something else") == "x"


def test_format_block_diff_added():
    """_format_block_diff detects added block."""
    old = {}
    new = {"foo": ("def foo():", "    return 1")}
    result = _format_block_diff(old, new, "src/test.py", "markdown")
    assert "ADDED" in result
    assert "foo" in result


def test_format_block_diff_deleted():
    """_format_block_diff detects deleted block."""
    old = {"foo": ("def foo():", "    return 1")}
    new = {}
    result = _format_block_diff(old, new, "src/test.py", "markdown")
    assert "DELETED" in result
    assert "foo" in result


def test_format_block_diff_unchanged():
    """_format_block_diff skips unchanged blocks."""
    old = {"foo": ("def foo():", "    return 1")}
    new = {"foo": ("def foo():", "    return 1")}
    result = _format_block_diff(old, new, "src/test.py", "markdown")
    assert "MODIFIED" not in result


def test_format_block_diff_signature_changed():
    """_format_block_diff detects signature change."""
    old = {"foo": ("def foo(x):", "    return x")}
    new = {"foo": ("def foo(x, y=0):", "    return x + y")}
    result = _format_block_diff(old, new, "src/test.py", "markdown")
    assert "Signature changed" in result


def test_format_block_diff_body_changed():
    """_format_block_diff detects body change."""
    old = {"foo": ("def foo():", "    return 1")}
    new = {"foo": ("def foo():", "    return 2")}
    result = _format_block_diff(old, new, "src/test.py", "markdown")
    assert "Body:" in result


def test_fallback_diff():
    """_fallback_diff uses text-based difflib."""
    result = _fallback_diff("old", "new", "test.txt", "markdown")
    assert "test.txt" in result
    assert "REMOVED" in result or "ADDED" in result


def test_structural_diff_javascript():
    """Structural diff works for JavaScript."""
    old = "function foo() {\n    return 1;\n}\n"
    new = "function foo() {\n    return 2;\n}\n"
    result = structural_diff(old, new, "src/app.js", "javascript", "markdown")
    assert "MODIFIED" in result


def test_structural_diff_ruby():
    """Structural diff works for Ruby."""
    old = "def foo\n    return 1\nend\n"
    new = "def foo\n    return 2\nend\n"
    result = structural_diff(old, new, "src/helper.rb", "ruby", "markdown")
    assert "MODIFIED" in result
