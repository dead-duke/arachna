"""Test structural diff for C-like code with braces in strings (ARCH-01 awareness)."""

from arachna.differ_structural import _parse_c_like_blocks, structural_diff


def test_c_like_braces_in_string_js():
    """JavaScript function with braces inside a string literal.

    Note: this documents the known ARCH-01 limitation —
    regex brace matching may incorrectly handle braces in strings.
    """
    text = (
        "function formatJSON() {\n"
        '    const template = "{\\"key\\": \\"value\\"}";\n'
        "    return JSON.parse(template);\n"
        "}\n"
    )
    blocks = _parse_c_like_blocks(text, "javascript")
    assert "formatJSON" in blocks


def test_c_like_braces_in_comment_js():
    """JS function with braces in a comment."""
    text = (
        "function process() {\n    // This function handles { and } characters\n    return 1;\n}\n"
    )
    blocks = _parse_c_like_blocks(text, "javascript")
    assert "process" in blocks


def test_structural_diff_c_like_handles_braces_in_strings():
    """Structural diff for JS with braces in strings produces output (doesn't crash)."""
    old = 'function fmt() {\n    return "{\\"a\\": 1}";\n}\n'
    new = 'function fmt() {\n    return "{\\"a\\": 2}";\n}\n'
    result = structural_diff(old, new, "src/fmt.js", "javascript")
    assert isinstance(result, str)
    assert len(result) > 0
