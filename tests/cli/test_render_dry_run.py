import io
import sys

from arachna.cli.renderer import render_dry_run


def test_single_part():
    stats = [
        {
            "name": "c",
            "name_tmpl": "chat",
            "max_tokens": 16000,
            "parts": [{"part_num": 1, "total_tokens": 5000, "sections": [("a.py", 3000)]}],
        }
    ]
    out = io.StringIO()
    old = sys.stdout
    sys.stdout = out
    render_dry_run(stats)
    sys.stdout = old
    assert "chat.md" in out.getvalue()
    assert "chat_1" not in out.getvalue()


def test_multiple_parts():
    stats = [
        {
            "name": "c",
            "name_tmpl": "chat",
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
    v = out.getvalue()
    assert "chat_1.md" in v
    assert "chat_2.md" in v


def test_multiple_profiles():
    stats = [
        {
            "name": "a",
            "name_tmpl": "ca",
            "max_tokens": 16000,
            "parts": [{"part_num": 1, "total_tokens": 100, "sections": [("x.py", 100)]}],
        },
        {
            "name": "b",
            "name_tmpl": "cb",
            "max_tokens": 16000,
            "parts": [{"part_num": 1, "total_tokens": 200, "sections": [("y.py", 200)]}],
        },
    ]
    out = io.StringIO()
    old = sys.stdout
    sys.stdout = out
    render_dry_run(stats)
    sys.stdout = old
    v = out.getvalue()
    assert "[a] section" in v
    assert "[b] section" in v


def test_empty():
    stats = [{"name": "e", "name_tmpl": "ce", "max_tokens": 16000, "parts": []}]
    out = io.StringIO()
    old = sys.stdout
    sys.stdout = out
    render_dry_run(stats)
    sys.stdout = old
    assert "[e] section" in out.getvalue()
