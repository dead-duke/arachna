"""Test command mode with compress in _assemble_content."""

from arachna.gatherer import _assemble_content
from arachna.tokenizer import count_tokens


def test_command_mode_with_compress(tmp_path):
    profile = {
        "command": "echo 'hello\n\n\n\nworld'",
        "max_tokens": 16000,
        "split_mode": "by_paragraph",
        "compress": True,
    }

    named_sections, parts, _indices, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(parts) == 1
    assert "\n\n\n\n" not in parts[0]


def test_command_mode_without_compress(tmp_path):
    profile = {
        "command": "echo 'hello\n\n\n\nworld'",
        "max_tokens": 16000,
        "split_mode": "by_paragraph",
        "compress": False,
    }

    named_sections, parts, _indices, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(parts) == 1
    assert "hello" in parts[0]
    assert "world" in parts[0]
