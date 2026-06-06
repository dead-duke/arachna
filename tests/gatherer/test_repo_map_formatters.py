"""Tests for repo-map formatting helpers in gatherer.py."""

from arachna.gatherer import _format_json_sigs, _format_markdown_sigs, _format_xml_sigs


def test_format_markdown_sigs_with_lang(tmp_path):
    """Markdown signatures with language code fence."""
    f = tmp_path / "main.py"
    sigs = "def foo():\n    ...\n\nclass Bar:\n    ..."
    result = _format_markdown_sigs(f, "python", sigs)
    assert "### " in result
    assert "```python" in result
    assert "def foo():" in result
    assert "class Bar:" in result


def test_format_markdown_sigs_no_lang(tmp_path):
    """Markdown signatures without language."""
    f = tmp_path / "script"
    sigs = "function main()"
    result = _format_markdown_sigs(f, "", sigs)
    assert "```" in result
    assert "```python" not in result


def test_format_xml_sigs_with_lang(tmp_path):
    """XML signatures with language attribute."""
    f = tmp_path / "main.py"
    sigs = "def foo():\n    ..."
    result = _format_xml_sigs(f, "python", sigs)
    assert '<file path="' in result
    assert 'language="python"' in result
    assert "<![CDATA[" in result
    assert "def foo():" in result


def test_format_xml_sigs_no_lang(tmp_path):
    """XML signatures without language attribute."""
    f = tmp_path / "script"
    sigs = "function main()"
    result = _format_xml_sigs(f, "", sigs)
    assert '<file path="' in result
    assert "language=" not in result


def test_format_json_sigs_with_lang(tmp_path):
    """JSON signatures with language key."""
    import json

    f = tmp_path / "main.py"
    sigs = "def foo():\n    ..."
    result = _format_json_sigs(f, "python", sigs)
    data = json.loads(result)
    assert data["language"] == "python"
    assert data["path"] == str(f)
    assert "def foo():" in data["content"]


def test_format_json_sigs_no_lang(tmp_path):
    """JSON signatures without language key."""
    import json

    f = tmp_path / "script"
    sigs = "function main()"
    result = _format_json_sigs(f, "", sigs)
    data = json.loads(result)
    assert "language" not in data
    assert data["path"] == str(f)
