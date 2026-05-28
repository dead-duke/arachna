import json
from unittest.mock import patch

from arachna.__main__ import main


def test_list(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    with patch("sys.argv", ["arachna", "--list"]):
        main()
