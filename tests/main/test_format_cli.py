import json
from unittest.mock import patch

from arachna.__main__ import main


def test_format_xml(tmp_path, monkeypatch):
    """--format xml produces XML output."""
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    with patch("sys.argv", ["arachna", "--profile", "c", "--format", "xml"]):
        main()
    files = list((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert '<file path="' in content
    assert "<![CDATA[" in content


def test_format_json(tmp_path, monkeypatch):
    """--format json produces JSON output."""
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    with patch("sys.argv", ["arachna", "--profile", "c", "--format", "json"]):
        main()
    files = list((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert '"path":' in content
    assert '"content":' in content


def test_format_default_is_markdown(tmp_path, monkeypatch):
    """Default format is markdown with code fences."""
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    with patch("sys.argv", ["arachna", "--profile", "c"]):
        main()
    files = list((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "```python" in content
