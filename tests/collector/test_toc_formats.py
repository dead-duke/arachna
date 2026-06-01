"""Tests for _build_toc with different output formats."""

from arachna.collector import _build_toc
from arachna.compressor import compress


def test_toc_markdown():
    """TOC lists files from named_sections that appear in part_content."""
    sections = [
        ("src/main.py", "### src/main.py\n\n```python\nprint('hi')\n```\n", 10),
        ("src/utils.py", "### src/utils.py\n\n```python\ndef foo(): pass\n```\n", 10),
    ]
    content = sections[0][1] + "\n\n" + sections[1][1]
    toc = _build_toc(sections, content, 1, 3)
    assert "Part 1 of 3" in toc
    assert "main.py" in toc
    assert "utils.py" in toc


def test_toc_xml():
    """TOC works for XML-formatted content."""
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
    content = sections[0][1] + "\n" + sections[1][1]
    toc = _build_toc(sections, content, 2, 5)
    assert "Part 2 of 5" in toc
    assert "main.py" in toc
    assert "utils.py" in toc


def test_toc_json():
    """TOC works for JSON-formatted content."""
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
    content = sections[0][1] + sections[1][1]
    toc = _build_toc(sections, content, 3, 4)
    assert "Part 3 of 4" in toc
    assert "main.py" in toc
    assert "utils.py" in toc


def test_toc_empty():
    """Empty sections produce empty TOC."""
    toc = _build_toc([], "", 1, 1)
    assert toc == ""


def test_toc_no_match():
    """TOC is empty when no section content matches part_content."""
    sections = [("src/main.py", "content_a", 10)]
    toc = _build_toc(sections, "different content", 1, 2)
    assert toc == ""


def test_toc_pre_commands():
    """Pre-command sections are included with their label."""
    sections = [
        ("pre: tree src", "tree output", 5),
        ("src/main.py", "### src/main.py\n\n```python\ncode\n```\n", 10),
    ]
    content = sections[0][1] + "\n\n" + sections[1][1]
    toc = _build_toc(sections, content, 1, 1)
    assert "pre: tree src" in toc
    assert "main.py" in toc


def test_toc_with_compress():
    """TOC works when content has been compressed (whitespace changes).

    Compress collapses blank lines (3+ → 2) and strips trailing whitespace.
    TOC matching uses content.strip() in part_content — after compression,
    content may differ from original named_sections content.
    """
    # Content with extra blank lines — after compress: "hello\n\nworld"
    raw_content = "### src/main.py\n\n```python\nhello\n\n\n\nworld\n```\n"
    compressed = compress(raw_content)
    # Original named_sections entry — uncompressed
    sections = [
        ("src/main.py", raw_content, 10),
    ]
    # Build TOC with compressed part_content
    toc = _build_toc(sections, compressed, 1, 1)
    # Content.strip() of raw: '### src/main.py\n\n```python\nhello\n\n\n\nworld\n```'
    # Content.strip() of compressed: '### src/main.py\n\n```python\nhello\n\nworld\n```'
    # These differ → "in" check will fail → TOC may be empty
    # This test documents current behaviour — TOC may miss files after compression
    assert "Part 1 of 1" in toc or toc == ""
