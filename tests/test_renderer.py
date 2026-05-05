"""Tests for renderer — output formatting."""

import io
import sys

from arachna.renderer import _format_line, render_dry_run


def test_format_line_basic():
    result = _format_line(500, 16000, "main.py")
    assert "500 tokens" in result
    assert "3.1%" in result
    assert "main.py" in result
    assert "|" in result


def test_format_line_zero_tokens():
    result = _format_line(0, 16000, "empty.py")
    assert "0 tokens" in result
    assert "<0.1%" in result


def test_format_line_full_limit():
    result = _format_line(16000, 16000, "full.py")
    assert "100.0%" in result


def test_format_line_small_percentage():
    result = _format_line(1, 32000, "tiny.py")
    assert "<0.1%" in result


def test_format_line_zero_max_tokens():
    result = _format_line(100, 0, "test.py")
    assert "0.0%" in result


def test_format_line_long_name():
    result = _format_line(100, 1000, "a" * 80)
    assert "a" * 80 in result


def test_render_dry_run_single_part():
    stats = [
        {
            "name": "code",
            "name_tmpl": "chat-code",
            "max_tokens": 16000,
            "parts": [
                {
                    "part_num": 1,
                    "total_tokens": 5000,
                    "sections": [("main.py", 3000), ("utils.py", 2000)],
                }
            ],
        }
    ]
    out = io.StringIO()
    old = sys.stdout
    sys.stdout = out
    render_dry_run(stats)
    sys.stdout = old
    output = out.getvalue()
    assert "[code] section" in output
    assert "chat-code_1.md" in output
    assert "5000 tokens" in output
    assert "main.py" in output


def test_render_dry_run_multiple_parts():
    stats = [
        {
            "name": "code",
            "name_tmpl": "chat-code",
            "max_tokens": 100,
            "parts": [
                {"part_num": 1, "total_tokens": 100, "sections": [("a.py", 100)]},
                {"part_num": 2, "total_tokens": 50, "sections": [("b.py", 50)]},
            ],
        }
    ]
    out = io.StringIO()
    old = sys.stdout
    sys.stdout = out
    render_dry_run(stats)
    sys.stdout = old
    output = out.getvalue()
    assert "chat-code_1.md" in output
    assert "chat-code_2.md" in output
    assert output.count("===") >= 2


def test_render_dry_run_multiple_profiles():
    stats = [
        {
            "name": "code",
            "name_tmpl": "chat-code",
            "max_tokens": 16000,
            "parts": [{"part_num": 1, "total_tokens": 100, "sections": [("main.py", 100)]}],
        },
        {
            "name": "tests",
            "name_tmpl": "chat-tests",
            "max_tokens": 16000,
            "parts": [{"part_num": 1, "total_tokens": 200, "sections": [("test_main.py", 200)]}],
        },
    ]
    out = io.StringIO()
    old = sys.stdout
    sys.stdout = out
    render_dry_run(stats)
    sys.stdout = old
    output = out.getvalue()
    assert "[code] section" in output
    assert "[tests] section" in output


def test_render_dry_run_empty_parts():
    stats = [
        {
            "name": "empty",
            "name_tmpl": "chat-empty",
            "max_tokens": 16000,
            "parts": [],
        }
    ]
    out = io.StringIO()
    old = sys.stdout
    sys.stdout = out
    render_dry_run(stats)
    sys.stdout = old
    output = out.getvalue()
    assert "[empty] section" in output
