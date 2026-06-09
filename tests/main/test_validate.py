import json
from unittest.mock import patch

from arachna.__main__ import main


def test_valid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    with patch("sys.argv", ["arachna", "collect", "--validate"]), patch("sys.exit") as ex:
        main()
        ex.assert_called_with(0)


def test_invalid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {"b": {"max_tokens": 0}}}))
    with patch("sys.argv", ["arachna", "collect", "--validate"]), patch("sys.exit") as ex:
        main()
        ex.assert_called_with(1)
