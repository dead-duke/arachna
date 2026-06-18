"""Tests for _write_diff_parts in collector.py (v1.7.1)."""

from arachna.domain.api_types import DiffSection
from arachna.domain.collector import _write_diff_parts
from arachna.domain.tokenizer import count_tokens


def test_write_diff_parts_single_file(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    sections = [
        DiffSection(
            type="modified",
            path="src/main.py",
            content="### src/main.py\n\nREMOVED lines 1:\n    old\n\nADDED lines 1:\n    new\n",
        ),
    ]
    created = _write_diff_parts(
        sections,
        out,
        "chat-diff",
        "# Test — DIFF from snap1 (part {part} of {total})\n\n",
        "Test",
        32768,
        count_tokens,
    )
    assert len(created) == 1
    assert "chat-diff_1.md" in created[0]


def test_write_diff_parts_multiple_files(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    big = "x" * 2000
    sections = [
        DiffSection(
            type="modified", path="a.py", content=f"### a.py\n\nREMOVED lines 1:\n    {big}\n"
        ),
        DiffSection(
            type="modified", path="b.py", content=f"### b.py\n\nADDED lines 1:\n    {big}\n"
        ),
    ]
    created = _write_diff_parts(
        sections,
        out,
        "chat-diff",
        "# Test — DIFF (part {part} of {total})\n\n",
        "Test",
        50,
        count_tokens,
    )
    assert len(created) >= 2


def test_write_diff_parts_empty_sections(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    created = _write_diff_parts(
        [],
        out,
        "chat-diff",
        "# Test (part {part} of {total})\n\n",
        "Test",
        32768,
        count_tokens,
    )
    assert created == []


def test_write_diff_parts_empty_content(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    sections = [
        DiffSection(type="modified", path="empty.py", content=""),
        DiffSection(
            type="modified", path="real.py", content="### real.py\n\nADDED lines 1:\n    code\n"
        ),
    ]
    _write_diff_parts(
        sections,
        out,
        "chat-diff",
        "# Test (part {part} of {total})\n\n",
        "Test",
        32768,
        count_tokens,
    )
    content = (out / "chat-diff_1.md").read_text()
    assert "real.py" in content


def test_write_diff_parts_with_toc(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    sections = [
        DiffSection(
            type="modified",
            path="src/main.py",
            content="### src/main.py\n\nREMOVED lines 1:\n    old\n",
        ),
        DiffSection(
            type="added",
            path="src/new.py",
            content="### src/new.py\n\nADDED (new file):\n\n```\nnew\n```\n",
        ),
    ]
    _write_diff_parts(
        sections,
        out,
        "chat-diff",
        "# Test (part {part} of {total})\n\n",
        "Test",
        32768,
        count_tokens,
    )
    content = (out / "chat-diff_1.md").read_text()
    assert "Part 1 of 1" in content
    assert "main.py" in content
    assert "new.py" in content


def test_write_diff_parts_toc_built_from_names(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    sections = [
        DiffSection(
            type="added",
            path="src/auth.py",
            content="### src/auth.py\n\nADDED (new file):\n\n```\nx = 1\n```\n",
        ),
        DiffSection(
            type="added",
            path="src/login.py",
            content="### src/login.py\n\nADDED (new file):\n\n```\nx = 1\n```\n",
        ),
    ]
    _write_diff_parts(
        sections,
        out,
        "chat-diff",
        "# Test (part {part} of {total})\n\n",
        "Test",
        32768,
        count_tokens,
    )
    content = (out / "chat-diff_1.md").read_text()
    assert "auth.py" in content
    assert "login.py" in content
