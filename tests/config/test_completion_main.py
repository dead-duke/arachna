"""Test for config/completion.py main() function."""

import sys
from io import StringIO
from unittest.mock import patch

from arachna.config.completion import main


def test_main_no_args_prints_usage():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    with patch("sys.argv", ["completion"]):
        main()
    sys.stdout = old
    output = out.getvalue()
    assert "source <(arachna completion bash)" in output
    assert "source <(arachna completion zsh)" in output
