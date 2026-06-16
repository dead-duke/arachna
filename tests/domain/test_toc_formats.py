"""Tests for _build_toc with different output formats."""

from arachna.domain.collector import _build_toc


def test_toc_markdown():
    """TOC lists files from named_sections for given indices."""
    sections = [
        ("src/main.py", "### src/main.py\n\n```python\nprint('hi')\n```\n", 10),
        ("src/utils.py", "### src/utils.py\n\n```python\ndef foo(): pass\n```\n", 10),
    ]
    toc = _build_toc(sections, [0, 1], 1, 3)
    assert "Part 1 of 3" in toc
    assert "main.py" in toc
    assert "utils.py" in toc


def test_toc_xml():
    """TOC works for XML-formatted content with section indices."""
    sections = [
        (
            "src/main.py",
            '<file path="src/main.py" language="python">\n<![CDATA[\nprint("hi")\n]]>\n</file>\n',
            10,
        ),
        (
            "src/utils.py",
            '<file path="src/utils.py" language="python">\n<![CDATA[\ndef foo(): pass\n]]>\n</file>\n',
            10,
        ),
    ]
    toc = _build_toc(sections, [0, 1], 2, 5)
    assert "Part 2 of 5" in toc
    assert "main.py" in toc
    assert "utils.py" in toc


def test_toc_json():
    """TOC works for JSON-formatted content with section indices."""
    sections = [
        (
            "src/main.py",
            '{"path": "src/main.py", "language": "python", "content": "print(\\"hi\\")"}\n',
            10,
        ),
        (
            "src/utils.py",
            '{"path": "src/utils.py", "language": "python", "content": "def foo(): pass"}\n',
            10,
        ),
    ]
    toc = _build_toc(sections, [0, 1], 3, 4)
    assert "Part 3 of 4" in toc
    assert "main.py" in toc
    assert "utils.py" in toc


def test_toc_empty():
    """Empty indices produce empty TOC."""
    toc = _build_toc([], [], 1, 1)
    assert toc == ""


def test_toc_no_indices():
    """No matching indices produces empty TOC."""
    sections = [("src/main.py", "content_a", 10)]
    toc = _build_toc(sections, [], 1, 2)
    assert toc == ""


def test_toc_pre_commands():
    """Pre-command sections are included with their label."""
    sections = [
        ("pre: tree src", "tree output", 5),
        ("src/main.py", "### src/main.py\n\n```python\ncode\n```\n", 10),
    ]
    toc = _build_toc(sections, [0, 1], 1, 1)
    assert "pre: tree src" in toc
    assert "main.py" in toc


def test_toc_with_compress():
    """TOC works correctly after compression — built from names, not content matching."""
    raw_content = "### src/main.py\n\n```python\nhello\n\n\n\nworld\n```\n"
    sections = [
        ("src/main.py", raw_content, 10),
    ]
    toc = _build_toc(sections, [0], 1, 1)
    assert "Part 1 of 1" in toc
    assert "main.py" in toc
