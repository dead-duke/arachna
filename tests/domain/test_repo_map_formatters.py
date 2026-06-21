"""Tests for repo-map formatting helpers in formatter.py."""

from arachna.domain.formatting.formatter import (
    _format_sigs_json,
    _format_sigs_markdown,
    _format_sigs_xml,
)


def test_format_markdown_sigs_with_lang(tmp_path):
    f = tmp_path / "main.py"
    sigs = "def foo():\n    ...\n\nclass Bar:\n    ..."
    result = _format_sigs_markdown(f, "python", sigs)
    assert "### " in result
    assert "```python" in result
    assert "def foo():" in result
    assert "class Bar:" in result


def test_format_markdown_sigs_no_lang(tmp_path):
    f = tmp_path / "script"
    sigs = "function main()"
    result = _format_sigs_markdown(f, "", sigs)
    assert "```" in result
    assert "```python" not in result


def test_format_xml_sigs_with_lang(tmp_path):
    f = tmp_path / "main.py"
    sigs = "def foo():\n    ..."
    result = _format_sigs_xml(f, "python", sigs)
    assert '<file path="' in result
    assert 'language="python"' in result
    assert "<![CDATA[" in result
    assert "def foo():" in result


def test_format_xml_sigs_no_lang(tmp_path):
    f = tmp_path / "script"
    sigs = "function main()"
    result = _format_sigs_xml(f, "", sigs)
    assert '<file path="' in result
    assert "language=" not in result


def test_format_json_sigs_with_lang(tmp_path):
    import json

    f = tmp_path / "main.py"
    sigs = "def foo():\n    ..."
    result = _format_sigs_json(f, "python", sigs)
    data = json.loads(result)
    assert data["language"] == "python"
    assert data["path"] == str(f)
    assert "def foo():" in data["content"]


def test_format_json_sigs_no_lang(tmp_path):
    import json

    f = tmp_path / "script"
    sigs = "function main()"
    result = _format_sigs_json(f, "", sigs)
    data = json.loads(result)
    assert "language" not in data
    assert data["path"] == str(f)
