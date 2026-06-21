import tempfile
from pathlib import Path

from arachna.domain.formatting.formatter import format_file_section


def test_shebang_env_no_args():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "script"
        f.write_text("#!/usr/bin/env\nprint('hello')")
        result = format_file_section(f)
        assert "```" in result


def test_shebang_unknown_binary():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "script"
        f.write_text("#!/usr/bin/unknown_binary\nprint('hello')")
        result = format_file_section(f)
        assert "```" in result
