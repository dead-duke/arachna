import tempfile
from pathlib import Path

from arachna.domain.formatting.formatter import format_file_section


def test_python_shebang():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "script"
        f.write_text("#!/usr/bin/env python3\nprint('hi')")
        assert "```python" in format_file_section(f)


def test_bash_shebang():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "script"
        f.write_text("#!/bin/bash\necho hi")
        assert "```bash" in format_file_section(f)


def test_node_shebang():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "script"
        f.write_text("#!/usr/bin/env node\nconsole.log('hi')")
        assert "```javascript" in format_file_section(f)


def test_no_shebang():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "script"
        f.write_text("just text")
        assert "```" in format_file_section(f)


def test_extension_wins():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "script.py"
        f.write_text("#!/bin/bash\necho hi")
        assert "```python" in format_file_section(f)
